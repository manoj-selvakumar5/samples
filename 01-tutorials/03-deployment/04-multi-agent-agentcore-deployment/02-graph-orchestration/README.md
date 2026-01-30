# Graph-Based Multi-Agent Orchestration with Amazon Bedrock AgentCore

This tutorial demonstrates how to deploy a graph-based multi-agent e-commerce assistant to Amazon Bedrock AgentCore using Strands Agents SDK GraphBuilder for deterministic routing across distributed runtimes.

![Architecture](./images/architecture.png)

| Feature | Description |
|---------|-------------|
| Deployment target | Amazon Bedrock AgentCore Runtime (5 runtimes) |
| Orchestration | Strands Agents GraphBuilder DAG with conditional edges |
| Agent types | Classifier (A2A), Product (A2A), Order (A2A+MCP), Recommendation (A2A), Graph Orchestrator (HTTP) |
| Model | Claude Sonnet 4 via Amazon Bedrock |

## Prerequisites

- Python 3.10 or higher
- AWS CLI configured with appropriate permissions
- Docker or Podman installed (optional if using CodeBuild)
- Claude Sonnet 4 model access in Amazon Bedrock
- IAM permissions to:
  - Create IAM roles and policies
  - Create Amazon ECR repositories
  - Deploy Amazon Bedrock AgentCore runtimes
  - Write to AWS Systems Manager Parameter Store
  - Create and manage DynamoDB tables

## Tutorial Structure

| Notebook | Agent | Description |
|----------|-------|-------------|
| [01-deploy-classifier-agent.ipynb](./01-deploy-classifier-agent.ipynb) | Classifier Agent | Pure LLM agent that classifies customer intent into BROWSE, ORDER, or RECOMMEND |
| [02-deploy-product-agent.ipynb](./02-deploy-product-agent.ipynb) | Product Agent | A2A server with HTTP API tools for product catalog search |
| [03-deploy-order-agent.ipynb](./03-deploy-order-agent.ipynb) | Order Agent | A2A server with MCP integration for DynamoDB order lookup |
| [04-deploy-recommendation-agent.ipynb](./04-deploy-recommendation-agent.ipynb) | Recommendation Agent | Pure LLM synthesis agent for personalized product recommendations |
| [05-deploy-graph-orchestrator.ipynb](./05-deploy-graph-orchestrator.ipynb) | Graph Orchestrator | GraphBuilder DAG that routes through all agents with conditional edges |

## Architecture Components

| Agent | Protocol | Port | Tools | Purpose |
|-------|----------|------|-------|---------|
| Classifier | A2A | 9000 | None | Classifies customer intent into BROWSE, ORDER, or RECOMMEND |
| Product | A2A | 9000 | DummyJSON API | Searches product catalog by keyword or category |
| Order | A2A | 9000 | DynamoDB via MCP | Looks up customer orders and order history |
| Recommendation | A2A | 9000 | None | Generates personalized recommendations from predecessor context |
| Graph Orchestrator | HTTP | 8080 | GraphBuilder + A2A clients | Coordinates all agents via GraphBuilder DAG |

## Graph Topology

```
classifier_node --> product_node         (BROWSE or RECOMMEND)
classifier_node --> order_node           (ORDER or RECOMMEND)
product_node    --> recommendation_node  (RECOMMEND only)
order_node      --> recommendation_node  (RECOMMEND only)
```

### 3 Execution Paths

| Intent | Path | Agents Invoked |
|--------|------|----------------|
| BROWSE | Classifier -> Product | 2 |
| ORDER | Classifier -> Order | 2 |
| RECOMMEND | Classifier -> Product + Order (parallel) -> Recommendation | 4 |

## Key Concepts

### GraphBuilder
Strands Agents GraphBuilder creates a DAG (Directed Acyclic Graph) for deterministic multi-agent routing. Unlike dynamic orchestration where an LLM decides routing at each step, GraphBuilder defines all possible paths upfront. Condition functions evaluate graph state to determine which edges to traverse.

### Conditional Routing
The Classifier outputs structured JSON (`{"intent": "BROWSE|ORDER|RECOMMEND"}`). Three condition functions parse this intent from `GraphState` to determine which downstream agents execute.

### Parallel Execution
For RECOMMEND intent, Product and Order agents are independent nodes in the same execution batch. GraphBuilder automatically runs them concurrently, reducing total latency.

### Join/Fan-in
The Recommendation node depends on both Product and Order nodes. GraphBuilder's `_build_node_input()` waits for all predecessors to complete and passes their combined outputs as context.

### A2A Protocol
The Agent-to-Agent (A2A) protocol enables structured communication between agents using JSON-RPC 2.0 format. Each graph node is a local Agent that uses `A2AClientToolProvider` to forward requests to a remote A2A agent on its own AgentCore runtime.

### SigV4 Authentication
All inter-agent calls are signed with AWS Signature Version 4 for authentication. The `SigV4HTTPXAuth` class handles signing for A2A requests to AgentCore endpoints.

### MCP with Async Lifespan
The Order Agent uses Model Context Protocol (MCP) with stdio transport for DynamoDB access. FastAPI's async lifespan pattern defers MCP subprocess startup until after port binding, ensuring health checks pass immediately.

### SSM Parameter Store for Discovery
Agent runtime URLs are stored in AWS Systems Manager Parameter Store under the `/ecommerce-graph/` prefix, enabling agents to discover each other at runtime.

## Running the Tutorial

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the notebooks in order:
   - **Notebook 1**: Deploy Classifier Agent
   - **Notebook 2**: Deploy Product Agent
   - **Notebook 3**: Deploy Order Agent (creates DynamoDB table with sample data)
   - **Notebook 4**: Deploy Recommendation Agent
   - **Notebook 5**: Deploy Graph Orchestrator and test all 3 execution paths

3. Test the system through the Graph Orchestrator endpoint with queries like:
   - "Show me laptops under $1000" (BROWSE path)
   - "What are my recent orders?" (ORDER path)
   - "Based on my purchase history, what would you recommend?" (RECOMMEND path)

## Project Structure

```
02-graph-orchestration/
├── 01-deploy-classifier-agent.ipynb
├── 02-deploy-product-agent.ipynb
├── 03-deploy-order-agent.ipynb
├── 04-deploy-recommendation-agent.ipynb
├── 05-deploy-graph-orchestrator.ipynb
├── requirements.txt
├── README.md
├── classifier_agent/
│   ├── a2a_server.py
│   └── requirements.txt
├── product_agent/
│   ├── a2a_server.py
│   └── requirements.txt
├── order_agent/
│   ├── a2a_server.py
│   └── requirements.txt
├── recommendation_agent/
│   ├── a2a_server.py
│   └── requirements.txt
├── graph_orchestrator/
│   ├── graph_agent.py              # GraphBuilder DAG definition
│   ├── app.py                      # BedrockAgentCoreApp HTTP entrypoint
│   ├── sigv4_auth.py               # SigV4 authentication for A2A calls
│   └── requirements.txt
├── utils/
│   ├── config.py                   # SSM paths and agent names
│   ├── iam.py                      # IAM role creation
│   ├── ssm_helpers.py              # Parameter Store helpers
│   ├── dynamodb_setup.py           # DynamoDB table setup
│   ├── sigv4_auth.py               # SigV4 authentication
│   ├── streaming.py                # Graph event display utilities
│   └── callbacks.py                # Tool logging callback handlers
├── sample_data/
│   └── orders.json
└── images/
    └── architecture.png
```

## Cleanup

Each notebook includes a cleanup section at the end. Notebook 5 includes a comprehensive cleanup cell that destroys all AWS resources across the entire tutorial:
- AgentCore runtimes (5 runtimes)
- ECR repositories
- IAM roles
- SSM parameters
- DynamoDB table

## Comparison with 01-a2a-orchestration

| Feature | 01-a2a-orchestration | 02-graph-orchestration |
|---------|---------------------|------------------------|
| Runtimes | 3 | 5 |
| Routing | Dynamic (LLM-decided) | Deterministic (GraphBuilder DAG) |
| Parallelism | None | Product + Order run in parallel |
| Intent Classification | Orchestrator handles inline | Dedicated Classifier Agent |
| Recommendations | Not supported | Dedicated Recommendation Agent |
| Graph features | N/A | Conditional routing, parallel execution, join, chaining |

## Additional Resources

- [Strands Agents GraphBuilder Documentation](https://strandsagents.com/latest/user-guide/concepts/multi-agent/graphs/)
- [Strands Agents A2A Documentation](https://strandsagents.com/latest/user-guide/concepts/multi-agent/a2a/)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [Strands Agents MCP Integration](https://strandsagents.com/latest/user-guide/concepts/tools/mcp-tools/)
- [Deploy to Amazon Bedrock AgentCore](https://strandsagents.com/latest/user-guide/deploy/deploy_to_bedrock_agentcore/)
