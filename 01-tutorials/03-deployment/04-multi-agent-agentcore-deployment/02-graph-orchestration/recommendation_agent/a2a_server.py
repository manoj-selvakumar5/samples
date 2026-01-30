"""Recommendation Agent deployed to Amazon Bedrock AgentCore with A2A protocol support.

Synthesizes personalized product recommendations using context from graph predecessor
nodes. Receives product catalog data and order history via GraphBuilder's
_build_node_input() and generates tailored suggestions without any external tool calls.

Key features:
- A2A protocol server for graph-based multi-agent orchestration via Agent-to-Agent messaging
- Pure LLM synthesis with no tools -- all reasoning from predecessor node context
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
SSM_RECOMMENDATION_AGENT_URL = "/ecommerce-graph/recommendation-agent-url"

SYSTEM_PROMPT = """You are a Recommendation Agent for an e-commerce assistant.

You receive context from upstream agents in a graph-based orchestration pipeline:
- Product catalog data (available products with names, categories, prices, ratings)
- Customer order history (past purchases with dates, quantities, totals)

Your task is to generate personalized product recommendations by cross-referencing
the customer's purchase patterns and browsing interests with the available catalog.

Instructions:
1. Analyze the customer's purchase patterns from their order history.
2. Cross-reference past purchases with available products in the catalog.
3. Generate 3-5 personalized product recommendations with clear explanations.
4. For each recommendation, include:
   - Product name
   - Category
   - Why it is recommended (based on purchase history or product attributes)
   - Price, if available from the catalog data
5. If you receive only product data (no order history), recommend popular or
   highly-rated products from the catalog.
6. If you receive only order data (no product catalog), suggest complementary
   products based on past purchase categories and patterns.
7. Keep recommendations concise and conversational.
"""


class ToolLoggingHandler:
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


# Get AWS region
session = boto3.Session()
region = session.region_name or os.environ.get("AWS_REGION", "us-west-2")

recommendation_agent = Agent(
    name="Ecommerce_Graph_Recommendation",
    description="Personalized product recommendation agent for e-commerce assistant",
    system_prompt=SYSTEM_PROMPT,
    model=BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[],
    callback_handler=ToolLoggingHandler(),
)

app = FastAPI()

@app.get("/ping")
async def health():
    return {"status": "healthy"}

a2a_server = A2AServer(agent=recommendation_agent, serve_at_root=True)
a2a_server.setup(app)

if __name__ == "__main__":
    logger.info(f"Starting Recommendation Agent on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
