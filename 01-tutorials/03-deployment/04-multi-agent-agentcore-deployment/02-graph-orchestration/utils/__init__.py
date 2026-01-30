"""Utility modules for graph orchestration multi-agent deployment to Amazon Bedrock AgentCore.

Provides configuration constants, IAM role management, DynamoDB setup, SSM helpers,
and streaming display utilities for Classifier, Product, Order, Recommendation,
and Graph Orchestrator agent deployment and operation.

Modules:
- config: SSM paths, agent names, and deployment configuration constants
- iam: IAM execution role creation and deletion for Amazon Bedrock AgentCore
- ssm_helpers: Store and retrieve agent URLs from AWS Systems Manager Parameter Store
- dynamodb_setup: Create, seed, and clean up DynamoDB orders table
- callbacks: Tool invocation logging callback handler
- streaming: Graph execution event display utilities
"""

from .config import (
    SSM_CLASSIFIER_AGENT_URL,
    SSM_PRODUCT_AGENT_URL,
    SSM_ORDER_AGENT_URL,
    SSM_RECOMMENDATION_AGENT_URL,
    SSM_ORDERS_TABLE,
    DYNAMODB_TABLE_NAME,
    CLASSIFIER_AGENT_NAME,
    PRODUCT_AGENT_NAME,
    ORDER_AGENT_NAME,
    RECOMMENDATION_AGENT_NAME,
    ORCHESTRATOR_AGENT_NAME,
    CLASSIFIER_ROLE_NAME,
    PRODUCT_ROLE_NAME,
    ORDER_ROLE_NAME,
    RECOMMENDATION_ROLE_NAME,
    ORCHESTRATOR_ROLE_NAME,
)
from .iam import create_agentcore_role, delete_agentcore_role
from .ssm_helpers import store_agent_url, get_agent_url, delete_agent_url
from .dynamodb_setup import create_orders_table, seed_orders, delete_orders_table

__all__ = [
    "SSM_CLASSIFIER_AGENT_URL",
    "SSM_PRODUCT_AGENT_URL",
    "SSM_ORDER_AGENT_URL",
    "SSM_RECOMMENDATION_AGENT_URL",
    "SSM_ORDERS_TABLE",
    "DYNAMODB_TABLE_NAME",
    "CLASSIFIER_AGENT_NAME",
    "PRODUCT_AGENT_NAME",
    "ORDER_AGENT_NAME",
    "RECOMMENDATION_AGENT_NAME",
    "ORCHESTRATOR_AGENT_NAME",
    "CLASSIFIER_ROLE_NAME",
    "PRODUCT_ROLE_NAME",
    "ORDER_ROLE_NAME",
    "RECOMMENDATION_ROLE_NAME",
    "ORCHESTRATOR_ROLE_NAME",
    "create_agentcore_role",
    "delete_agentcore_role",
    "store_agent_url",
    "get_agent_url",
    "delete_agent_url",
    "create_orders_table",
    "seed_orders",
    "delete_orders_table",
]
