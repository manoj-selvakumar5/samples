"""Product Agent deployed to Amazon Bedrock AgentCore with A2A protocol support.

Queries product catalog from DummyJSON API (https://dummyjson.com) using custom
tools built with the Strands @tool decorator.

Key features:
- A2A protocol server for graph-based multi-agent orchestration via Agent-to-Agent messaging
- Custom HTTP request tools for external API access
- OpenTelemetry instrumentation for AWS X-Ray distributed tracing
"""

import json
import logging
import os
from typing import Any

import boto3
import requests
import uvicorn
from fastapi import FastAPI
from strands import Agent, tool
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from strands.telemetry import StrandsTelemetry

logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

StrandsTelemetry().setup_otlp_exporter()

PORT = 9000
SSM_PRODUCT_AGENT_URL = "/ecommerce-graph/product-agent-url"

SYSTEM_PROMPT = """You are a Product Agent for an e-commerce assistant.

You have access to tools that query a product catalog with 194+ products across multiple categories.

Available tools:
- search_products: Search for products by keyword (e.g., "laptop", "phone")
- get_products_by_category: Get products from specific categories
- get_all_products: Browse all available products

Electronics categories available:
- laptops (MacBook Pro, Dell XPS, ThinkPad, etc.)
- smartphones (iPhone, Samsung, Google Pixel, etc.)
- tablets (iPad, Samsung Tab, etc.)
- mobile-accessories (phone cases, chargers, etc.)

Other categories: beauty, fragrances, furniture, groceries, mens-shirts, womens-dresses, and more.

Help customers find products by searching, browsing categories, or filtering by price.
If a product isn't found, suggest similar alternatives from available categories.
"""

@tool
def search_products(query: str, limit: int = 10) -> str:
    """Search for products by keyword across all categories.

    Args:
        query: Search term (e.g., "laptop", "phone", "MacBook")
        limit: Maximum number of products to return (default: 10)

    Returns:
        JSON string with matching products including id, title, price, category, description
    """
    try:
        url = f"https://dummyjson.com/products/search?q={query}&limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        products = data.get("products", [])
        result = []
        for p in products:
            result.append({
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "description": p.get("description", ""),
                "rating": p.get("rating", 0),
            })
        return json.dumps({"products": result, "total": data.get("total", 0)})
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_products_by_category(category: str, limit: int = 10) -> str:
    """Get products from a specific category.

    Args:
        category: Category name (e.g., "laptops", "smartphones", "beauty")
        limit: Maximum number of products to return (default: 10)

    Returns:
        JSON string with products in the specified category
    """
    try:
        url = f"https://dummyjson.com/products/category/{category}?limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        products = data.get("products", [])
        result = []
        for p in products:
            result.append({
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "description": p.get("description", ""),
                "rating": p.get("rating", 0),
            })
        return json.dumps({"products": result, "total": len(result)})
    except Exception as e:
        logger.error(f"Error getting category {category}: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_all_products(limit: int = 30) -> str:
    """Browse all available products in the catalog.

    Args:
        limit: Maximum number of products to return (default: 30)

    Returns:
        JSON string with product listings
    """
    try:
        url = f"https://dummyjson.com/products?limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        products = data.get("products", [])
        result = []
        for p in products:
            result.append({
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "rating": p.get("rating", 0),
            })
        return json.dumps({"products": result, "total": data.get("total", 0)})
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return json.dumps({"error": str(e)})


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

product_agent = Agent(
    name="Ecommerce_Graph_Product",
    description="Product catalog search agent for e-commerce assistant",
    system_prompt=SYSTEM_PROMPT,
    model=BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[search_products, get_products_by_category, get_all_products],
    callback_handler=ToolLoggingHandler(),
)

app = FastAPI()

@app.get("/ping")
async def health():
    return {"status": "healthy"}

a2a_server = A2AServer(agent=product_agent, serve_at_root=True)
a2a_server.setup(app)

if __name__ == "__main__":
    logger.info(f"Starting Product Agent on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
