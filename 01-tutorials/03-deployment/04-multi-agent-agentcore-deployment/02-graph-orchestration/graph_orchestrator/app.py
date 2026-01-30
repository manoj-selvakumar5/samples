"""Graph Orchestrator application deployed to Amazon Bedrock AgentCore with HTTP protocol.

Uses GraphBuilder DAG for deterministic routing of customer queries through
classifier, product, order, and recommendation agents deployed to AgentCore.

Entry point for the graph-based multi-agent e-commerce assistant. Receives HTTP
requests, executes the graph DAG, and streams results back to the caller.
"""

import json
import logging
import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.telemetry import StrandsTelemetry

from graph_agent import create_graph

# --- Logging ---

logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

StrandsTelemetry().setup_otlp_exporter()

# --- Configuration ---

SSM_CLASSIFIER_AGENT_URL = "/ecommerce-graph/classifier-agent-url"
SSM_PRODUCT_AGENT_URL = "/ecommerce-graph/product-agent-url"
SSM_ORDER_AGENT_URL = "/ecommerce-graph/order-agent-url"
SSM_RECOMMENDATION_AGENT_URL = "/ecommerce-graph/recommendation-agent-url"

app = BedrockAgentCoreApp()


# --- Helper ---


def get_agent_url(ssm_param: str, env_var: str) -> str:
    """Get agent URL from environment variable or SSM Parameter Store.

    Args:
        ssm_param: SSM parameter name for the agent URL.
        env_var: Environment variable name to check first.

    Returns:
        Agent runtime invocation URL.
    """
    if url := os.environ.get(env_var):
        return url
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=ssm_param, WithDecryption=True)
    return response["Parameter"]["Value"]


# --- Initialize Graph ---

logger.info("Initializing graph orchestrator...")

classifier_url = get_agent_url(SSM_CLASSIFIER_AGENT_URL, "CLASSIFIER_AGENT_URL")
product_url = get_agent_url(SSM_PRODUCT_AGENT_URL, "PRODUCT_AGENT_URL")
order_url = get_agent_url(SSM_ORDER_AGENT_URL, "ORDER_AGENT_URL")
recommendation_url = get_agent_url(SSM_RECOMMENDATION_AGENT_URL, "RECOMMENDATION_AGENT_URL")

logger.info(f"Classifier URL: {classifier_url}")
logger.info(f"Product URL: {product_url}")
logger.info(f"Order URL: {order_url}")
logger.info(f"Recommendation URL: {recommendation_url}")

graph = create_graph(classifier_url, product_url, order_url, recommendation_url)

logger.info("Graph orchestrator initialized")


# --- Entrypoint ---


@app.entrypoint
async def invoke(payload):
    """Handle incoming requests by executing the graph DAG.

    The graph automatically:
    1. Runs classifier to determine intent (BROWSE, ORDER, RECOMMEND)
    2. Routes to appropriate agents based on conditional edges
    3. Executes independent agents in parallel (Product + Order for RECOMMEND)
    4. Chains results through recommendation node when needed

    Args:
        payload: Request dictionary with 'prompt' and optional 'customer_id'.

    Yields:
        Structured event dictionaries for streaming display.
    """
    user_input = payload.get("prompt", "")
    customer_id = payload.get("customer_id", "CUST-101")

    logger.info(f"=== INCOMING REQUEST === Customer: {customer_id}")
    logger.info(f"Prompt: {user_input}")

    # Execute graph with streaming
    async for event in graph.stream_async(user_input):
        if isinstance(event, dict):
            # Node lifecycle events
            if "multi_agent_node_start" in event:
                node_id = event["multi_agent_node_start"].get("node_id", "")
                logger.info(f">> Node started: {node_id}")
                yield json.dumps({"type": "node_start", "node_id": node_id}) + "\n"

            elif "multi_agent_node_stop" in event:
                node_id = event["multi_agent_node_stop"].get("node_id", "")
                logger.info(f"<< Node completed: {node_id}")
                yield json.dumps({"type": "node_stop", "node_id": node_id}) + "\n"

            elif "multi_agent_node_stream" in event:
                # Forward inner agent streaming events
                inner = event.get("multi_agent_node_stream", {})
                node_id = inner.get("node_id", "")
                inner_event = inner.get("event", {})

                # Extract text from nested Amazon Bedrock Converse API events
                if isinstance(inner_event, dict) and "event" in inner_event:
                    bedrock_event = inner_event["event"]
                    if "contentBlockDelta" in bedrock_event:
                        delta = bedrock_event["contentBlockDelta"].get("delta", {})
                        if "text" in delta:
                            yield json.dumps({
                                "type": "text",
                                "content": delta["text"],
                                "node_id": node_id,
                            }) + "\n"

            elif "result" in event:
                # Final graph result with execution metrics
                result = event["result"]
                yield json.dumps({
                    "type": "graph_complete",
                    "total_nodes": getattr(result, "total_nodes", 0),
                    "completed_nodes": getattr(result, "completed_nodes", 0),
                    "execution_time": getattr(result, "execution_time", 0),
                }) + "\n"

    logger.info("=== GRAPH EXECUTION COMPLETE ===")


if __name__ == "__main__":
    app.run()
