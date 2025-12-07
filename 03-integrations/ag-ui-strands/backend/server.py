"""Minimal AG-UI + Strands Agent Example.

This demonstrates how to expose a Strands agent via the AG-UI protocol,
enabling real-time streaming to any AG-UI compatible frontend (CopilotKit, etc).
"""

from strands import Agent
from strands.models import BedrockModel
from ag_ui_strands import StrandsAgent, create_strands_app

# Create a Strands agent with Amazon Bedrock
model = BedrockModel(model_id="amazon.nova-lite-v1:0")

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant. Keep responses concise and friendly.",
)

# Wrap with AG-UI adapter - this translates Strands events to AG-UI protocol events
agui_agent = StrandsAgent(
    agent=agent,
    name="strands-chat",
    description="A simple Strands agent exposed via AG-UI protocol",
)

# Create FastAPI app with CORS enabled for local development
app = create_strands_app(agui_agent, "/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
