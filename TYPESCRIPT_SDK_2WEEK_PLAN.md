# TypeScript SDK - 2 Week Launch Plan

**Focus**: Get developers started with TypeScript SDK quickly
**Scope**: Current features only (no full Python parity needed)
**Timeline**: 2 weeks to initial release

---

## Current TypeScript SDK Features

✅ **Agent class** - Basic agent initialization and execution
✅ **Function tools** - Custom tool creation
✅ **Bedrock model provider** - Amazon Bedrock models
✅ **OpenAI model provider** - OpenAI models
✅ **Streamed response** - Async streaming
✅ **Agent state** - Session/state management

🔒 **Embargoed** (for later release): MCP, Built-in tools, Hooks, Conversation manager

---

## Week 1: Core Tutorials (5 tutorials)

### Day 1-2: Getting Started
**Tutorial 1: First TypeScript Agent** (`typescript/01-tutorials/01-fundamentals/01-first-agent/`)
- Files: `README.md`, `basic-agent.ts`, `package.json`
- Content:
  - Install SDK with npm/pnpm
  - Create basic agent with Bedrock
  - Simple system prompt
  - Run first agent query
  - Handle response

### Day 2-3: Tools
**Tutorial 2: Custom Tools** (`typescript/01-tutorials/01-fundamentals/02-custom-tools/`)
- Files: `README.md`, `custom-tools.ts`, `tools/calculator.ts`
- Content:
  - Define TypeScript tool functions
  - Tool parameter types
  - Tool result handling
  - Multiple tools example
  - Real-world tool (weather API, database query, etc.)

### Day 3-4: Models
**Tutorial 3: Model Providers** (`typescript/01-tutorials/01-fundamentals/03-model-providers/`)
- Files: `README.md`, `bedrock.ts`, `openai.ts`
- Content:
  - Configure Bedrock models (Claude, etc.)
  - Configure OpenAI models
  - Switch between providers
  - Model parameters (temperature, max_tokens)

### Day 4-5: Streaming
**Tutorial 4: Streaming Responses** (`typescript/01-tutorials/01-fundamentals/04-streaming/`)
- Files: `README.md`, `streaming.ts`, `callbacks.ts`
- Content:
  - Async streaming patterns
  - Handle streamed tokens
  - Event handlers/callbacks
  - Show progress in real-time

### Day 5: State Management
**Tutorial 5: Agent State** (`typescript/01-tutorials/01-fundamentals/05-agent-state/`)
- Files: `README.md`, `state-management.ts`
- Content:
  - Maintain conversation context
  - Session persistence
  - State across multiple calls
  - Stateful vs stateless agents

---

## Week 2: Samples & Deployment (4 items)

### Day 6-7: Sample 1
**Customer Support Agent** (`typescript/02-samples/01-customer-support/`)
- Files: `README.md`, `agent.ts`, `tools/kb-search.ts`, `tools/ticket.ts`
- Features used:
  - Single agent
  - Custom tools (search knowledge base, create ticket)
  - Bedrock model
  - State management for conversation
- Real-world scenario developers can relate to

### Day 7-8: Sample 2
**Code Assistant** (`typescript/02-samples/02-code-assistant/`)
- Files: `README.md`, `agent.ts`, `tools/file-ops.ts`
- Features used:
  - Custom file reading tool
  - Code analysis helper
  - OpenAI model (GPT-4)
  - Streaming for long responses
- Practical developer use case

### Day 8-9: Sample 3
**Research Assistant** (`typescript/02-samples/03-research-assistant/`)
- Files: `README.md`, `agent.ts`, `tools/web-search.ts`, `tools/summarize.ts`
- Features used:
  - Multiple custom tools
  - Agent composition (if ready)
  - Bedrock Knowledge Base integration (if simple)
  - State to track research progress
- Business use case

### Day 9-10: Deployment
**Deployment Guide** (`typescript/01-tutorials/03-deployment/`)
- Files: `README.md`, `01-lambda-deployment/`, `02-express-server/`
- Content:
  - **Lambda example**: Simple handler.ts, deployment script
  - **Express/Fastify server**: REST API wrapper
  - Environment variables
  - Basic error handling
  - Not full CDK, just working examples

---

## Directory Structure

```
typescript/
├── README.md                                      # Overview, getting started, feature status
├── 01-tutorials/
│   ├── README.md                                  # Tutorial overview and learning path
│   ├── 01-fundamentals/                           # Week 1: Core concepts
│   │   ├── README.md                              # Fundamentals overview
│   │   ├── 01-first-agent/
│   │   ├── 02-custom-tools/
│   │   ├── 03-model-providers/
│   │   ├── 04-streaming/
│   │   └── 05-agent-state/
│   ├── 02-multi-agent-systems/                    # Future: Multi-agent patterns
│   │   ├── README.md                              # Coming soon note
│   │   ├── 01-agent-as-tool/                      # Placeholder
│   │   ├── 02-swarm-agent/                        # Placeholder
│   │   └── 03-graph-agent/                        # Placeholder
│   └── 03-deployment/                             # Week 2: Production deployment
│       ├── README.md                              # Deployment overview
│       ├── 01-lambda-deployment/
│       └── 02-express-server/
├── 02-samples/                                    # Real-world use cases
│   ├── 01-customer-support/
│   ├── 02-code-assistant/
│   └── 03-research-assistant/
├── 03-integrations/                               # Future: Third-party integrations
│   └── README.md                                  # Placeholder
├── 04-UX-demos/                                   # Future: Full-stack demos
│   └── README.md                                  # Placeholder
└── 05-agentic-rag/                                # Future: RAG patterns
    └── README.md                                  # Placeholder
```

**Total Deliverables (Week 1-2)**: 5 fundamentals + 2 deployment + 3 samples = 10 items

**Note**: Structure matches Python samples repository for consistency. Placeholder sections (multi-agent-systems, integrations, UX-demos, agentic-rag) will be populated as features become available.

---

## Structure Alignment with Python Samples

The TypeScript samples structure **exactly mirrors** the Python samples for consistency and ease of navigation:

### Comparison

| Category | Python Path | TypeScript Path | Status |
|----------|-------------|-----------------|--------|
| **Fundamentals** | `01-tutorials/01-fundamentals/` | `01-tutorials/01-fundamentals/` | ✅ Week 1-2 |
| **Multi-Agent** | `01-tutorials/02-multi-agent-systems/` | `01-tutorials/02-multi-agent-systems/` | 📅 Placeholder |
| **Deployment** | `01-tutorials/03-deployment/` | `01-tutorials/03-deployment/` | ✅ Week 1-2 |
| **Samples** | `02-samples/` | `02-samples/` | ✅ Week 1-2 |
| **Integrations** | `03-integrations/` | `03-integrations/` | 📅 Placeholder |
| **UX Demos** | `04-UX-demos/` | `04-UX-demos/` | 📅 Placeholder |
| **Agentic RAG** | `05-agentic-rag/` | `05-agentic-rag/` | 📅 Placeholder |

### Benefits of This Structure

1. **Cross-SDK Navigation**: Developers using both Python and TypeScript can easily find equivalent tutorials
2. **Clear Organization**: Three-tier structure (fundamentals → multi-agent → deployment) shows natural learning progression
3. **Future-Ready**: Placeholder sections indicate roadmap without cluttering current content
4. **Scalability**: Easy to add new tutorials in appropriate categories as features ship

### Mapping Python Tutorials to TypeScript

| Python Tutorial | Python Code | TypeScript Equivalent | TypeScript Status |
|----------------|-------------|----------------------|-------------------|
| F1: First Agent | ✅ Available | 01-fundamentals/01-first-agent | ✅ Week 1 |
| F2: Model Providers | ✅ Available | 01-fundamentals/03-model-providers | ✅ Week 1 |
| F3: AWS Services | ✅ Available | 01-fundamentals/ (in samples) | ✅ Week 2 (in samples) |
| F4a: MCP Tools | ✅ Available | 01-fundamentals/06-mcp-integration | 🔒 Embargoed |
| F4b: Custom Tools | ✅ Available | 01-fundamentals/02-custom-tools | ✅ Week 1 |
| F5: Streaming | ✅ Available | 01-fundamentals/04-streaming | ✅ Week 1 |
| F6: Guardrails | ✅ Available | - | ❌ Not planned |
| F7: Memory | ✅ Available | 01-fundamentals/09-conversation-manager | 📅 Future |
| F8: Observability | ✅ Available | 01-fundamentals/08-hooks | 🔒 Embargoed |
| M1: Agent as Tool | ✅ Available | 02-multi-agent-systems/01-agent-as-tool | 📅 Future |
| M2: Swarm | ✅ Available | 02-multi-agent-systems/02-swarm-agent | 📅 Future |
| M3: Graph | ✅ Available | 02-multi-agent-systems/03-graph-agent | 📅 Future |
| D1: Lambda | ✅ Available | 03-deployment/01-lambda-deployment | ✅ Week 2 |
| D2: Fargate | ✅ Available | 03-deployment/02-express-server | ✅ Week 2 (alternative) |

---

## Standards & Guidelines

### Each Tutorial/Sample Includes:

**README.md Structure**:
```markdown
# Title
## What You'll Learn
## Prerequisites (Node.js version, AWS account if needed)
## Installation
## Code Walkthrough
## Running the Example
## Next Steps
```

**Code Standards**:
- TypeScript with strict mode
- Async/await patterns
- Proper error handling
- Comments explaining key concepts
- `.env.example` for configuration

**Package.json**:
```json
{
  "name": "@strands-samples/example-name",
  "type": "module",
  "scripts": {
    "dev": "tsx src/index.ts",
    "build": "tsc"
  },
  "dependencies": {
    "@strands/agents": "latest"
  }
}
```

### Keep It Simple:
- ❌ No complex architecture diagrams (unless really needed)
- ❌ No CDK deployment stacks (just simple scripts)
- ❌ No trying to replicate every Python example
- ✅ Clear, runnable code
- ✅ Practical examples
- ✅ Focus on TypeScript strengths
- ✅ Get developers productive quickly

---

## Main README Content

**`typescript/README.md`** should include:

1. **Quick Start** - Install SDK, run first agent in 5 minutes
2. **Feature Status Table**:
   ```
   | Feature | Status | Tutorial |
   |---------|--------|----------|
   | Agent class | ✅ Available | 01-fundamentals/01-first-agent |
   | Custom tools | ✅ Available | 01-fundamentals/02-custom-tools |
   | Bedrock models | ✅ Available | 01-fundamentals/03-model-providers |
   | OpenAI models | ✅ Available | 01-fundamentals/03-model-providers |
   | Streaming | ✅ Available | 01-fundamentals/04-streaming |
   | Agent state | ✅ Available | 01-fundamentals/05-agent-state |
   | Multi-agent patterns | 📅 Planned | 02-multi-agent-systems/ |
   | Lambda deployment | ✅ Available | 03-deployment/01-lambda-deployment |
   | Express server | ✅ Available | 03-deployment/02-express-server |
   | MCP tools | 🔒 Coming soon | - |
   | Built-in tools | 🔒 Coming soon | - |
   | Hooks | 🔒 Coming soon | - |
   | Conversation manager | 📅 Planned | - |
   ```
3. **Learning Path** - Tutorial order recommendation
4. **Samples by Use Case** - Which sample for which scenario
5. **Python vs TypeScript** - Key differences, why choose TypeScript

---

## Post-2-Week Plan: Embargoed Features (Ready After AWS Event)

### Week 3-4: Embargoed Tutorials (4 tutorials)

**Tutorial 6: MCP Integration** (`typescript/01-tutorials/01-fundamentals/06-mcp-integration/`)
- Files: `README.md`, `basic-mcp.ts`, `custom-mcp-server.ts`
- Content:
  - MCPClient setup in TypeScript
  - Connect to external MCP servers (stdio transport)
  - HTTP transport for MCP
  - Create custom MCP server in TypeScript
  - MCP tool discovery and usage
- **TypeScript Advantage**: Type-safe MCP protocol definitions, better async handling

**Tutorial 7: Built-in Tools** (`typescript/01-tutorials/01-fundamentals/07-builtin-tools/`)
- Files: `README.md`, `file-tools.ts`, `execution-tools.ts`, `web-tools.ts`
- Content:
  - File operations (file_read, file_write, editor)
  - Execution tools (python_repl if applicable, shell)
  - Web tools (http_request)
  - Think tool for reasoning
  - Calculator, current_time
  - Journal for logging
- **TypeScript Advantage**: Strong typing for tool inputs/outputs, IntelliSense support

**Tutorial 8: Hooks System** (`typescript/01-tutorials/01-fundamentals/08-hooks/`)
- Files: `README.md`, `basic-hooks.ts`, `logging-hook.ts`, `auth-hook.ts`, `rate-limit-hook.ts`
- Content:
  - Hook lifecycle (pre/post execution)
  - Custom logging hooks
  - Authentication/authorization hooks
  - Rate limiting middleware
  - Error handling hooks
  - Metrics collection hooks
- **TypeScript Advantage**: Type-safe hook interfaces, decorator patterns, middleware chaining

**Tutorial 9: Conversation Manager** (`typescript/01-tutorials/01-fundamentals/09-conversation-manager/`)
- Files: `README.md`, `basic-conversation.ts`, `persistent-sessions.ts`
- Content:
  - Multi-turn conversation management
  - Session persistence (Redis, DB)
  - Context window optimization
  - Conversation history serialization
- **TypeScript Advantage**: Type-safe conversation state, better session management with TS interfaces

### Week 3-4: TypeScript-Specific Samples (5 samples)

**Sample 4: Real-Time Chat Agent (WebSocket)** (`typescript/02-samples/04-realtime-chat-websocket/`)
- **Why TypeScript**: WebSocket server, Socket.io integration, real-time streaming
- Features:
  - Express + Socket.io server
  - Real-time agent responses streamed to frontend
  - Multiple concurrent user sessions
  - React/Vue chat UI (shared TypeScript types)
  - MCP tools for enhanced capabilities
- **Not possible in Python**: Same type definitions for frontend and backend
- Files: `server.ts`, `client/`, `shared-types.ts`, `agent.ts`

**Sample 5: Slack Bot with Hooks** (`typescript/02-samples/05-slack-bot/`)
- **Why TypeScript**: Slack Bolt SDK (TypeScript-first), hooks for auth/logging
- Features:
  - Slack app integration
  - Hooks for authentication
  - Hooks for audit logging
  - Custom tools for Slack operations
  - MCP server integration
- **Not possible in Python**: Better Slack SDK support, type-safe event handlers
- Files: `bot.ts`, `hooks/`, `tools/slack-tools.ts`, `mcp-servers/`

**Sample 6: Next.js AI Assistant** (`typescript/02-samples/06-nextjs-ai-assistant/`)
- **Why TypeScript**: Full-stack TypeScript, shared types, App Router, Server Actions
- Features:
  - Next.js 14+ App Router
  - Server Actions for agent calls
  - React Server Components
  - Streaming UI with AI responses
  - Built-in tools for data fetching
  - Conversation manager for sessions
- **Not possible in Python**: Full-stack type safety, server components, edge runtime
- Files: `app/`, `lib/agent.ts`, `lib/tools.ts`, `components/`

**Sample 7: Discord Bot with MCP** (`typescript/02-samples/07-discord-bot-mcp/`)
- **Why TypeScript**: Discord.js (TypeScript-native), better event handling
- Features:
  - Discord.js integration
  - Slash commands
  - MCP tools for external data
  - Built-in tools for Discord operations
  - Hooks for moderation
- **Not possible in Python**: Discord.js features, type-safe command handlers
- Files: `bot.ts`, `commands/`, `mcp-servers/`, `hooks/moderation.ts`

**Sample 8: API Gateway with Agent Router** (`typescript/02-samples/08-api-gateway-router/`)
- **Why TypeScript**: Express/Fastify middleware, tRPC integration, Zod validation
- Features:
  - RESTful API with multiple agent endpoints
  - tRPC for type-safe API contracts
  - Zod schema validation
  - Hooks for auth, rate limiting, logging
  - OpenAPI documentation
  - Multiple specialized agents routed by endpoint
- **Not possible in Python**: End-to-end type safety with tRPC, Zod validation
- Files: `server.ts`, `routes/`, `agents/`, `middleware/`, `schemas/`

**Sample 9: Vercel AI SDK Integration** (`typescript/02-samples/09-vercel-ai-sdk/`)
- **Why TypeScript**: Vercel AI SDK, Edge Runtime, streaming UI
- Features:
  - Integrate Strands Agents with Vercel AI SDK
  - Edge runtime deployment
  - Streaming responses to React UI
  - useChat hook integration
  - Built-in tools and MCP
- **Not possible in Python**: Vercel ecosystem, Edge Runtime
- Files: `app/api/chat/route.ts`, `app/page.tsx`, `lib/agent.ts`

---

## TypeScript-Specific Advantages & Sample Ideas

### 🎯 What TypeScript Enables (That Python Doesn't)

#### 1. **Full-Stack Type Safety**
**Advantage**: Share types between agent backend and frontend UI
**Sample Ideas**:
- ✅ Next.js AI Assistant (Sample 6)
- Remix AI app with shared types
- Nuxt.js Vue agent integration
- Astro content generation agent

#### 2. **Frontend Framework Integration**
**Advantage**: Direct integration with React, Vue, Svelte, Angular
**Sample Ideas**:
- ✅ Real-time Chat Agent (Sample 4)
- React Dashboard with agent widgets
- Vue admin panel with AI assistant
- Angular enterprise app with embedded agents

#### 3. **Real-Time & WebSocket**
**Advantage**: Node.js WebSocket ecosystem (Socket.io, ws)
**Sample Ideas**:
- ✅ WebSocket Chat (Sample 4)
- Multiplayer game with AI NPCs
- Collaborative document editing with AI
- Real-time trading assistant with WebSockets

#### 4. **Modern Web Frameworks & Tooling**
**Advantage**: Express, Fastify, NestJS, tRPC, Zod
**Sample Ideas**:
- ✅ API Gateway with Router (Sample 8)
- NestJS enterprise agent microservice
- tRPC monorepo with agents
- Hono edge runtime agent

#### 5. **Cloud & Edge Runtime**
**Advantage**: Vercel Edge, Cloudflare Workers, Deno Deploy
**Sample Ideas**:
- ✅ Vercel AI SDK Integration (Sample 9)
- Cloudflare Worker agent (global edge deployment)
- Deno Deploy agent (secure runtime)
- Bun runtime agent (ultra-fast startup)

#### 6. **Popular Bot Frameworks**
**Advantage**: Discord.js, Slack Bolt SDK, Telegram Bot API (TypeScript-first)
**Sample Ideas**:
- ✅ Discord Bot (Sample 7)
- ✅ Slack Bot (Sample 5)
- Telegram bot with inline queries
- WhatsApp Business API integration
- Microsoft Teams bot

#### 7. **Type-Safe API Contracts**
**Advantage**: tRPC, Zod, TypeBox for runtime validation
**Sample Ideas**:
- ✅ tRPC API Gateway (Sample 8)
- OpenAPI spec generation from types
- GraphQL API with typed resolvers
- JSON Schema validation with TypeBox

#### 8. **Better Async Patterns**
**Advantage**: Native Promise support, async/await, better concurrency
**Sample Ideas**:
- Event-driven agent orchestration
- Parallel agent execution with Promise.all
- Queue-based agent processing (BullMQ)
- Streaming aggregation patterns

#### 9. **Frontend Build Tooling**
**Advantage**: Vite, Turbopack, esbuild, SWC
**Sample Ideas**:
- Vite plugin for agent development
- Chrome extension with embedded agent
- Electron desktop app with AI
- Tauri desktop app (Rust + TS)

#### 10. **Node.js Ecosystem**
**Advantage**: npm packages (2M+), better web tooling
**Sample Ideas**:
- PDF generation agent (pdfkit, puppeteer)
- Email agent (nodemailer)
- Image processing agent (sharp)
- Video processing agent (ffmpeg)
- CSV/Excel agent (xlsx, papaparse)

---

## Enhanced Sample Ideas (TypeScript-Specific)

### Additional Sample Ideas for Future

**Enterprise/Production**:
1. **Multi-Tenant SaaS Agent Platform** - NestJS, PostgreSQL, Redis, hooks for tenant isolation
2. **Monitoring Dashboard** - Real-time agent metrics, Grafana-style UI with WebSockets
3. **Agent Marketplace** - Registry of agents, MCP servers, discovery system

**Developer Tools**:
4. **VSCode Extension with Agent** - Language server protocol, code suggestions
5. **GitHub App/Bot** - PR reviews, code analysis, issue triage
6. **CLI Tool** - Commander.js, interactive prompts, agent-powered CLI

**Content & Media**:
7. **Content Management Agent** - Headless CMS integration, automated content generation
8. **Image Generation Pipeline** - DALL-E/Midjourney integration, batch processing
9. **Video Summarization** - Transcription, summarization, timestamps

**E-commerce & Business**:
10. **Shopify App** - Product recommendations, customer support, order management
11. **Stripe Payment Assistant** - Invoice generation, subscription management
12. **CRM Integration** - HubSpot/Salesforce agent, lead scoring

**IoT & Edge**:
13. **Edge Computing Agent** - Cloudflare Workers, process at the edge
14. **Raspberry Pi Agent** - Home automation, sensor data processing
15. **Mobile Backend** - React Native/Expo backend agent

---

## Recommended Final Sample List

### Phase 1 (Week 1-2) - 3 samples
1. ✅ Customer Support Agent - Basic single agent
2. ✅ Code Assistant - Developer use case
3. ✅ Research Assistant - Business use case

### Phase 2 (Week 3-4) - 5 TypeScript-specific samples
4. **Real-Time Chat Agent (WebSocket)** - Real-time streaming
5. **Next.js AI Assistant** - Full-stack type safety
6. **Slack Bot with Hooks** - Enterprise integration
7. **Discord Bot with MCP** - Community bot
8. **API Gateway with Router** - tRPC, multiple agents

### Phase 3 (Future)
9. Vercel AI SDK Integration
10. VSCode Extension
11. GitHub App
12. Multi-Tenant SaaS Platform
13. Cloudflare Edge Agent

---

## Future (Phase 3): Advanced Features

### When Available:
- Conversation manager tutorial
- Multi-agent patterns (Swarm, Graph)
- Advanced integrations
- More deployment options

---

## Success Criteria

**By End of Week 2**:
- ✅ 5 working tutorials developers can follow
- ✅ 3 practical samples showing real use cases
- ✅ 1 deployment guide with working code
- ✅ All code tested and runnable
- ✅ Clear README explaining what's available
- ✅ TypeScript developers can get started immediately

**Quality Over Quantity**:
- Better to have 9 excellent examples than 20 mediocre ones
- Each example should be copy-paste ready
- Focus on developer experience

---

## Day-by-Day Breakdown

| Day | Deliverable | Location | Files |
|-----|-------------|----------|-------|
| 1-2 | Tutorial 1: First Agent | 01-fundamentals/ | README, basic-agent.ts, package.json |
| 2-3 | Tutorial 2: Custom Tools | 01-fundamentals/ | README, custom-tools.ts, tools/ |
| 3-4 | Tutorial 3: Model Providers | 01-fundamentals/ | README, bedrock.ts, openai.ts |
| 4-5 | Tutorial 4: Streaming | 01-fundamentals/ | README, streaming.ts, callbacks.ts |
| 5 | Tutorial 5: Agent State | 01-fundamentals/ | README, state-management.ts |
| 6-7 | Sample 1: Customer Support | 02-samples/ | README, agent.ts, tools/ |
| 7-8 | Sample 2: Code Assistant | 02-samples/ | README, agent.ts, tools/ |
| 8-9 | Sample 3: Research Assistant | 02-samples/ | README, agent.ts, tools/ |
| 9-10 | Deployment: Lambda & Express | 03-deployment/ | README, 01-lambda/, 02-express-server/ |

---

## Notes

- **No Python parity pressure** - TypeScript SDK is its own thing
- **Start simple** - Add complexity later based on feedback
- **Developer-first** - Easy to understand, easy to run
- **Realistic timeline** - 2 weeks is aggressive but doable with focus
- **Room to grow** - This is v1, we'll add more over time

---

**Last Updated**: 2025-11-14
**Status**: Planning Phase
**Target Release**: 2 weeks from approval
