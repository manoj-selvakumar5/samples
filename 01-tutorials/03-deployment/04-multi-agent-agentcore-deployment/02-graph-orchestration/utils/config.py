# AWS Systems Manager Parameter Store Paths
# Use-case based prefix "/ecommerce-graph/" enables IAM policies to grant
# access to all parameters for this deployment using single wildcard pattern:
# "arn:aws:ssm:*:*:parameter/ecommerce-graph/*"

# This scopes permissions to only this multi-agent system without exposing
# unrelated SSM parameters. See utils/iam.py for IAM permission configuration.
SSM_CLASSIFIER_AGENT_URL = "/ecommerce-graph/classifier-agent-url"
SSM_PRODUCT_AGENT_URL = "/ecommerce-graph/product-agent-url"
SSM_ORDER_AGENT_URL = "/ecommerce-graph/order-agent-url"
SSM_RECOMMENDATION_AGENT_URL = "/ecommerce-graph/recommendation-agent-url"
SSM_ORDERS_TABLE = "/ecommerce-graph/orders-table"

# Amazon DynamoDB table name for order storage
DYNAMODB_TABLE_NAME = "ecommerce-graph-orders"

# Agent names must use underscores only, never hyphens
CLASSIFIER_AGENT_NAME = "ecommerce_graph_classifier"
PRODUCT_AGENT_NAME = "ecommerce_graph_product"
ORDER_AGENT_NAME = "ecommerce_graph_order"
RECOMMENDATION_AGENT_NAME = "ecommerce_graph_recommendation"
ORCHESTRATOR_AGENT_NAME = "ecommerce_graph_orchestrator"

# Role Names (derived from agent names)
CLASSIFIER_ROLE_NAME = f"{CLASSIFIER_AGENT_NAME}-role"
PRODUCT_ROLE_NAME = f"{PRODUCT_AGENT_NAME}-role"
ORDER_ROLE_NAME = f"{ORDER_AGENT_NAME}-role"
RECOMMENDATION_ROLE_NAME = f"{RECOMMENDATION_AGENT_NAME}-role"
ORCHESTRATOR_ROLE_NAME = f"{ORCHESTRATOR_AGENT_NAME}-role"
