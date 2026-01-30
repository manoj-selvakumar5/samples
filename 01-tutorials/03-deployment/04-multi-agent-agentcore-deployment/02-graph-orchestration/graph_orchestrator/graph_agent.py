"""Graph orchestrator for e-commerce multi-agent system.

Defines a GraphBuilder DAG that routes customer queries through 4 remote
agents deployed to Amazon Bedrock AgentCore:
1. Classifier: Determines intent (BROWSE, ORDER, RECOMMEND)
2. Product Agent: Searches product catalog via DummyJSON API
3. Order Agent: Looks up customer orders via DynamoDB MCP
4. Recommendation Agent: Generates personalized product recommendations

Graph topology:
  classifier_node -> product_node         (BROWSE or RECOMMEND)
  classifier_node -> order_node           (ORDER or RECOMMEND)
  product_node    -> recommendation_node  (RECOMMEND)
  order_node      -> recommendation_node  (RECOMMEND)

Execution paths:
  BROWSE:    Classifier -> Product (2 agents)
  ORDER:     Classifier -> Order (2 agents)
  RECOMMEND: Classifier -> Product + Order (parallel) -> Recommendation (4 agents)
"""

import logging
import re

import boto3
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import GraphBuilder
from strands.multiagent.graph import GraphState
from strands_tools.a2a_client import A2AClientToolProvider

from sigv4_auth import SigV4HTTPXAuth

logger = logging.getLogger(__name__)


# =============================================================================
# Intent Parsing
# =============================================================================


def _parse_classifier_intent(state: GraphState) -> str:
    """Extract intent from Classifier node result.

    The classifier outputs JSON: {"intent": "BROWSE|ORDER|RECOMMEND", "reasoning": "..."}
    Parses the result text to extract the intent string with fallback handling.

    Args:
        state: Current graph execution state containing node results.

    Returns:
        Intent string: BROWSE, ORDER, or RECOMMEND. Defaults to BROWSE.
    """
    classifier_result = state.results.get("classifier_node")
    if not classifier_result:
        logger.warning("No classifier result found, defaulting to BROWSE")
        return "BROWSE"

    result_text = str(classifier_result.result)

    # Try JSON parsing first
    try:
        json_match = re.search(r'\{[^}]*"intent"\s*:\s*"(\w+)"[^}]*\}', result_text)
        if json_match:
            intent = json_match.group(1).upper()
            if intent in ("BROWSE", "ORDER", "RECOMMEND"):
                logger.info(f"Parsed intent from JSON: {intent}")
                return intent
    except Exception:
        pass

    # Fallback: keyword detection in result text
    text_upper = result_text.upper()
    for intent in ["RECOMMEND", "ORDER", "BROWSE"]:
        if intent in text_upper:
            logger.info(f"Detected intent from text: {intent}")
            return intent

    logger.warning("Could not parse intent, defaulting to BROWSE")
    return "BROWSE"


# =============================================================================
# Condition Functions for Graph Edges
# =============================================================================


def should_route_to_product(state: GraphState) -> bool:
    """Route to Product Agent for BROWSE or RECOMMEND intents."""
    intent = _parse_classifier_intent(state)
    return intent in ("BROWSE", "RECOMMEND")


def should_route_to_order(state: GraphState) -> bool:
    """Route to Order Agent for ORDER or RECOMMEND intents."""
    intent = _parse_classifier_intent(state)
    return intent in ("ORDER", "RECOMMEND")


def should_route_to_recommendation(state: GraphState) -> bool:
    """Route to Recommendation Agent for RECOMMEND intent only."""
    intent = _parse_classifier_intent(state)
    return intent == "RECOMMEND"


# =============================================================================
# Node Agent Factory
# =============================================================================


def _create_a2a_node_agent(
    name: str,
    description: str,
    system_prompt: str,
    agent_url: str,
    auth: SigV4HTTPXAuth,
    region: str,
) -> Agent:
    """Create a local agent that forwards requests to a remote A2A agent.

    Each graph node needs its own Agent instance. The agent uses
    A2AClientToolProvider to discover and call the remote agent via A2A protocol.

    Args:
        name: Agent name for identification in graph execution logs.
        description: Agent description for graph node metadata.
        system_prompt: Instructions for forwarding behavior.
        agent_url: Amazon Bedrock AgentCore invocation URL for the remote agent.
        auth: SigV4 authentication handler for AgentCore API calls.
        region: AWS region for Amazon Bedrock model invocation.

    Returns:
        Configured Agent instance ready for use as a graph node.
    """
    a2a_provider = A2AClientToolProvider(
        known_agent_urls=[agent_url],
        httpx_client_args={"auth": auth},
    )

    return Agent(
        name=name,
        description=description,
        system_prompt=system_prompt,
        model=BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name=region,
        ),
        tools=a2a_provider.tools,
    )


# =============================================================================
# Graph Construction
# =============================================================================


def create_graph(
    classifier_url: str,
    product_url: str,
    order_url: str,
    recommendation_url: str,
):
    """Create the graph orchestrator with 4 remote agent nodes.

    Constructs a GraphBuilder DAG where each node is a local Agent that
    forwards requests to a remote A2A agent on its own AgentCore runtime.
    Conditional edges determine which agents execute based on the Classifier's
    intent output.

    Args:
        classifier_url: AgentCore invocation URL for Classifier Agent.
        product_url: AgentCore invocation URL for Product Agent.
        order_url: AgentCore invocation URL for Order Agent.
        recommendation_url: AgentCore invocation URL for Recommendation Agent.

    Returns:
        Built Graph instance ready for execution via stream_async().
    """
    session = boto3.Session()
    region = session.region_name or "us-west-2"
    credentials = session.get_credentials()

    auth = SigV4HTTPXAuth(
        credentials=credentials,
        service="bedrock-agentcore",
        region=region,
    )

    # Create node agents - each wraps a remote A2A agent
    classifier_agent = _create_a2a_node_agent(
        name="Classifier_Node",
        description="Classifies customer intent into BROWSE, ORDER, or RECOMMEND",
        system_prompt=(
            "Forward the user's message to the classifier agent using the A2A tool. "
            "Return the classifier's response exactly as received. Do not modify or "
            "interpret the response."
        ),
        agent_url=classifier_url,
        auth=auth,
        region=region,
    )

    product_agent = _create_a2a_node_agent(
        name="Product_Node",
        description="Searches product catalog via DummyJSON API",
        system_prompt=(
            "Forward the user's request to the product agent using the A2A tool. "
            "Pass along any context about what products to search for. "
            "Return the product agent's response exactly as received."
        ),
        agent_url=product_url,
        auth=auth,
        region=region,
    )

    order_agent = _create_a2a_node_agent(
        name="Order_Node",
        description="Looks up customer orders from DynamoDB",
        system_prompt=(
            "Forward the user's request to the order agent using the A2A tool. "
            "Include any customer context if available. "
            "Return the order agent's response exactly as received."
        ),
        agent_url=order_url,
        auth=auth,
        region=region,
    )

    recommendation_agent = _create_a2a_node_agent(
        name="Recommendation_Node",
        description="Generates personalized product recommendations",
        system_prompt=(
            "Forward all context to the recommendation agent using the A2A tool. "
            "Include product catalog data and order history from previous nodes. "
            "Return the recommendation agent's response exactly as received."
        ),
        agent_url=recommendation_url,
        auth=auth,
        region=region,
    )

    # Build the graph DAG
    builder = GraphBuilder()

    # Add nodes
    builder.add_node(classifier_agent, "classifier_node")
    builder.add_node(product_agent, "product_node")
    builder.add_node(order_agent, "order_node")
    builder.add_node(recommendation_agent, "recommendation_node")

    # Add conditional edges
    # Classifier routes to Product for BROWSE and RECOMMEND intents
    builder.add_edge("classifier_node", "product_node", condition=should_route_to_product)
    # Classifier routes to Order for ORDER and RECOMMEND intents
    builder.add_edge("classifier_node", "order_node", condition=should_route_to_order)
    # Product and Order both route to Recommendation for RECOMMEND intent
    builder.add_edge("product_node", "recommendation_node", condition=should_route_to_recommendation)
    builder.add_edge("order_node", "recommendation_node", condition=should_route_to_recommendation)

    # Set entry point
    builder.set_entry_point("classifier_node")

    # Set execution timeout (graph involves multiple remote A2A calls)
    builder.set_execution_timeout(300.0)  # 5 minutes max

    # Build and return the graph
    graph = builder.build()

    logger.info("Graph orchestrator created with 4 nodes and 4 edges")
    logger.info("  classifier_node -> product_node (BROWSE, RECOMMEND)")
    logger.info("  classifier_node -> order_node (ORDER, RECOMMEND)")
    logger.info("  product_node -> recommendation_node (RECOMMEND)")
    logger.info("  order_node -> recommendation_node (RECOMMEND)")

    return graph
