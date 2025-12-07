# AG-UI + Strands Agents Example

A minimal example demonstrating how to connect a Strands agent to a React frontend using the [AG-UI protocol](https://github.com/ag-ui-protocol/ag-ui).

## What is AG-UI?

AG-UI (Agent-User Interaction Protocol) is an open, event-based protocol that standardizes how AI agents connect to user-facing applications. It enables:

- Real-time streaming of agent responses
- Bi-directional state synchronization
- Tool call visualization
- Human-in-the-loop interactions

## Architecture

```
┌─────────────────────┐         AG-UI Events (SSE)         ┌──────────────────────┐
│   React Frontend    │ ◄──────────────────────────────────│   Python Backend     │
│   (CopilotKit)      │                                    │   (FastAPI)          │
│                     │         HTTP POST + SSE            │                      │
│  @copilotkit/react  │ ────────────────────────────────► │  strands + ag_ui     │
└─────────────────────┘                                    └──────────────────────┘
                                                                     │
                                                                     ▼
                                                           ┌──────────────────────┐
                                                           │   Amazon Bedrock     │
                                                           │   (Claude Sonnet)    │
                                                           └──────────────────────┘
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- AWS credentials configured (for Amazon Bedrock access)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Quick Start

### 1. Start the Backend

```bash
cd backend

# Install dependencies and run
uv run uvicorn server:app --reload --port 8000
```

The AG-UI endpoint will be available at `http://localhost:8000`.

### 2. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open http://localhost:5173 to chat with the Strands agent.

## Project Structure

```
ag-ui-strands/
├── README.md
├── backend/
│   ├── pyproject.toml      # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── server.py           # FastAPI + Strands + AG-UI server
└── frontend/
    ├── package.json        # Node dependencies
    ├── tsconfig.json       # TypeScript config
    ├── vite.config.ts      # Vite build config
    ├── index.html          # HTML entry point
    └── src/
        ├── App.tsx         # CopilotKit chat interface
        └── main.tsx        # React entry point
```

## How It Works

1. **Backend** (`server.py`):
   - Creates a Strands `Agent` with Amazon Bedrock
   - Wraps it with `StrandsAgent` from `ag_ui_strands`
   - Exposes via `create_strands_app()` which sets up FastAPI with CORS

2. **Frontend** (`App.tsx`):
   - Uses `CopilotKit` component pointing to the backend URL
   - `CopilotChat` provides the chat UI with streaming support

3. **AG-UI Protocol**:
   - Frontend sends `RunAgentInput` via HTTP POST
   - Backend streams AG-UI events via SSE:
     - `RunStartedEvent`
     - `TextMessageStartEvent`, `TextMessageContentEvent`, `TextMessageEndEvent`
     - `ToolCallStartEvent`, `ToolCallEndEvent` (if tools are used)
     - `RunFinishedEvent`

## Customization

### Adding Tools

```python
from strands import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(
    model=model,
    tools=[get_weather],
    system_prompt="You can check the weather.",
)
```

### Changing the Model

```python
from strands.models import BedrockModel

# Use a different Claude model
model = BedrockModel(model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0")

# Or use a different provider
from strands.models import OpenAIModel
model = OpenAIModel(model_id="gpt-4o")
```

## Resources

- [AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui)
- [AG-UI Documentation](https://docs.ag-ui.com/)
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [CopilotKit](https://docs.copilotkit.ai/)
- [AG-UI Dojo (Live Demos)](https://dojo.ag-ui.com/aws-strands/feature/shared_state)
