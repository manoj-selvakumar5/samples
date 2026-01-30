"""AWS Systems Manager Parameter Store helper functions.

Provides utilities for storing and retrieving agent URLs and configuration
parameters used across the multi-agent tutorial notebooks.

Key functions:
- store_agent_url: Store agent runtime URLs in SSM Parameter Store
- get_agent_url: Retrieve agent URLs from SSM Parameter Store
- delete_parameters: Clean up SSM parameters during resource deletion
"""

import logging
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def store_agent_url(param_name: str, url: str, region: str) -> dict[str, Any]:
    """Store agent runtime URL in AWS Systems Manager Parameter Store.

    Uses SecureString type for encryption at rest. Overwrites existing
    parameter if present.

    Args:
        param_name: SSM parameter name (e.g., "/ecommerce-graph/order-agent-url").
        url: Agent runtime invocation URL from Amazon Bedrock AgentCore.
        region: AWS region for SSM client.

    Returns:
        Dictionary with parameter ARN and version information.
    """
    ssm = boto3.client("ssm", region_name=region)

    try:
        response = ssm.put_parameter(
            Name=param_name,
            Value=url,
            Type="SecureString",
            Overwrite=True,
        )
        logger.info(f"Stored parameter: {param_name}")
        return {
            "parameter_name": param_name,
            "version": response["Version"],
            "message": f"Stored parameter {param_name}",
        }
    except Exception as e:
        logger.error(f"Error storing parameter {param_name}: {e}")
        raise


def get_agent_url(param_name: str, region: str) -> str:
    """Retrieve agent runtime URL from AWS Systems Manager Parameter Store.

    Args:
        param_name: SSM parameter name to retrieve.
        region: AWS region for SSM client.

    Returns:
        Agent runtime URL string.
    """
    ssm = boto3.client("ssm", region_name=region)

    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        url = response["Parameter"]["Value"]
        logger.info(f"Retrieved parameter: {param_name}")
        return url
    except Exception as e:
        logger.error(f"Error retrieving parameter {param_name}: {e}")
        raise


def delete_parameters(param_names: list[str], region: str) -> dict[str, Any]:
    """Delete multiple SSM parameters.

    Args:
        param_names: List of SSM parameter names to delete.
        region: AWS region for SSM client.

    Returns:
        Dictionary with deletion results for each parameter.
    """
    ssm = boto3.client("ssm", region_name=region)

    results = {"deleted": [], "errors": []}

    logger.info(f"Deleting {len(param_names)} SSM parameters...")
    for param in param_names:
        try:
            ssm.delete_parameter(Name=param)
            logger.info(f"  Deleted: {param}")
            results["deleted"].append(param)
        except Exception as e:
            logger.error(f"  Error deleting {param}: {e}")
            results["errors"].append({"param": param, "error": str(e)})

    return {
        "deleted_count": len(results["deleted"]),
        "error_count": len(results["errors"]),
        "deleted": results["deleted"],
        "errors": results["errors"],
        "message": f"Deleted {len(results['deleted'])} parameters",
    }
