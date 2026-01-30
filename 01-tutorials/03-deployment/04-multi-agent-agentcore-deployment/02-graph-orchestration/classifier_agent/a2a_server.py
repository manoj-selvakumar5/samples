"""Classifier Agent deployed to Amazon Bedrock AgentCore with A2A protocol support.

Routes customer requests to the appropriate specialist agent by classifying intent
into BROWSE, ORDER, or RECOMMEND categories using structured JSON output.

Key features:
- A2A protocol server for graph-based multi-agent orchestration via Agent-to-Agent messaging
- Pure LLM classification with no tools -- relies on structured JSON output
- OpenTelemetry instrumentation for AWS X-Ray distributed tracing
"""

import json
import logging
import os

import boto3
import uvicorn
from fastapi import FastAPI
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from strands.telemetry import StrandsTelemetry

logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

StrandsTelemetry().setup_otlp_exporter()

PORT = 9000
SSM_CLASSIFIER_AGENT_URL = "/ecommerce-graph/classifier-agent-url"

SYSTEM_PROMPT = """You are a Classifier Agent for an e-commerce assistant.

Your ONLY job is to classify the customer's intent into exactly one of three categories.
You must respond with ONLY a JSON object, no other text.

Intent definitions:
- BROWSE: The customer wants to search, browse, or view products from the catalog.
- ORDER: The customer wants to check order status, order history, or shipment tracking.
- RECOMMEND: The customer wants product recommendations based on their purchase history AND the product catalog.

Output format (strict JSON, no markdown, no explanation outside the JSON):
{"intent": "BROWSE|ORDER|RECOMMEND", "reasoning": "brief explanation"}

Examples:
- "Show me laptops under $1000" -> {"intent": "BROWSE", "reasoning": "Customer wants to search the product catalog for laptops within a price range"}
- "Where is my order?" -> {"intent": "ORDER", "reasoning": "Customer is asking about order status or tracking"}
- "What should I buy next?" -> {"intent": "RECOMMEND", "reasoning": "Customer wants personalized product recommendations based on purchase history"}
- "I bought a camera last month, what accessories would go with it?" -> {"intent": "RECOMMEND", "reasoning": "Customer wants recommendations based on a previous purchase"}
- "Do you have wireless headphones?" -> {"intent": "BROWSE", "reasoning": "Customer wants to search the catalog for a specific product type"}
- "Show me my recent orders" -> {"intent": "ORDER", "reasoning": "Customer wants to view their order history"}
"""


class ToolLoggingHandler:
    """Log agent lifecycle events to Amazon CloudWatch Logs for debugging.

    Although the classifier agent uses no tools, this handler logs completion events
    to provide consistent observability across all agents in the multi-agent system.
    De-duplicates tool invocations by tracking toolUseId values.
    """

    def __init__(self):
        self.logged_tool_ids = set()
        self.tool_count = 0

    def __call__(self, **kwargs):
        message = kwargs.get("message", {})
        if isinstance(message, dict) and message.get("role") == "assistant":
            for content in message.get("content", []):
                if isinstance(content, dict):
                    tool_use = content.get("toolUse")
                    if tool_use:
                        tool_id = tool_use.get("toolUseId")
                        if tool_id and tool_id not in self.logged_tool_ids:
                            self.logged_tool_ids.add(tool_id)
                            self.tool_count += 1
                            logger.info(f"=== TOOL #{self.tool_count}: {tool_use.get('name', 'Unknown')} ===")
                            input_str = json.dumps(tool_use.get("input", {}))
                            if len(input_str) > 2000:
                                input_str = input_str[:2000] + "..."
                            logger.info(f"TOOL INPUT: {input_str}")
        if kwargs.get("complete") and kwargs.get("data"):
            logger.info(f"=== COMPLETE: {len(kwargs.get('data', ''))} chars ===")


# Get AWS region from boto3 session or environment variable
session = boto3.Session()
region = session.region_name or os.environ.get("AWS_REGION", "us-west-2")

classifier_agent = Agent(
    name="Ecommerce_Graph_Classifier",
    description="Intent classification agent for e-commerce assistant routing",
    system_prompt=SYSTEM_PROMPT,
    model=BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[],
    callback_handler=ToolLoggingHandler(),
)

# FastAPI app with health check endpoint for Amazon Bedrock AgentCore container monitoring
app = FastAPI()


@app.get("/ping")
async def health():
    return {"status": "healthy"}


# A2A server wraps the agent for inter-agent communication
a2a_server = A2AServer(agent=classifier_agent, serve_at_root=True)
a2a_server.setup(app)

if __name__ == "__main__":
    logger.info(f"Starting Classifier Agent on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
