# Deploying TypeScript-based Strands Agents to Amazon Bedrock AgentCore Runtime

**Last Updated**: 2025-11-17
**Status**: Implementation Guide
**Target Audience**: TypeScript/Node.js developers deploying Strands agents to production

---

## Overview

Amazon Bedrock AgentCore Runtime is a serverless managed runtime for deploying, scaling, and operating AI agents in production. This guide shows you how to deploy TypeScript-based Strands agents to AgentCore.

### What is Amazon Bedrock AgentCore?

- **Serverless Runtime**: No infrastructure management - AWS handles everything
- **Secure Isolation**: Dedicated microVMs for each user session
- **Auto-Scaling**: Automatically scales based on demand
- **Multi-Framework**: Works with Strands, LangGraph, CrewAI, and other frameworks
- **Model Agnostic**: Compatible with any LLM (Bedrock, OpenAI, Gemini, etc.)
- **Protocol Support**: Native A2A (Agent-to-Agent) and MCP (Model Context Protocol)

### Current Availability

- **Status**: Preview (FREE until September 16, 2025)
- **Regions**: US East (N. Virginia), US West (Oregon), Asia Pacific (Sydney), Europe (Frankfurt)
- **TypeScript Support**: ✅ Full support via npm SDK and containerization

---

## Why Use AgentCore for TypeScript Agents?

| Feature | AgentCore | Lambda | ECS Fargate |
|---------|-----------|--------|-------------|
| Infrastructure Management | Zero | Minimal | Medium |
| Streaming Support | ✅ Yes | ❌ No | ✅ Yes |
| Session Isolation | ✅ Built-in | Manual | Manual |
| Auto-Scaling | ✅ Automatic | ✅ Automatic | Requires config |
| Cost (Preview) | FREE | Pay per invoke | Pay per container |
| A2A Protocol | ✅ Native | ❌ No | Manual |
| Setup Time | Minutes | Minutes | Hours |

**Use AgentCore when you need:**
- Zero infrastructure management
- Built-in session isolation and security
- Native agent-to-agent communication
- Quick production deployment
- Free preview testing

---

## Prerequisites

### Required Tools

```bash
# Node.js and npm
node --version  # v18+ recommended
npm --version

# AWS CLI
aws --version  # v2.x recommended

# Docker (for containerized approach)
docker --version

# Optional: AWS CDK for infrastructure-as-code
npm install -g aws-cdk
```

### AWS Requirements

- AWS Account with appropriate permissions
- IAM role with permissions for:
  - Amazon Bedrock (model invocation)
  - Amazon ECR (container registry)
  - Amazon Bedrock AgentCore Runtime
  - CloudWatch Logs

### TypeScript Strands SDK

```bash
npm install @strands/agents
npm install @aws-sdk/client-bedrock-agentcore
```

---

## Technical Requirements

### Container Specifications

| Requirement | Value | Notes |
|-------------|-------|-------|
| **Platform** | `linux/arm64` | ARM architecture only (cost-effective) |
| **Port** | `8080` | Fixed port requirement |
| **Endpoints** | `/invocations`, `/ping` | Mandatory API endpoints |
| **Session IDs** | 33+ characters | Required for proper VM isolation |
| **Registry** | Amazon ECR | Container images must be in ECR |

### Required API Endpoints

#### 1. POST /invocations
```typescript
// Agent interaction endpoint
POST /invocations
Content-Type: application/json

{
  "sessionId": "unique-session-id-33-chars-minimum",
  "input": "User message to the agent"
}

Response:
{
  "sessionId": "unique-session-id-33-chars-minimum",
  "response": "Agent response",
  "metadata": { ... }
}
```

#### 2. GET /ping
```typescript
// Health check endpoint
GET /ping

Response:
200 OK
"OK" or { "status": "healthy" }
```

---

## Deployment Approaches

### Approach A: SDK Integration (Recommended for Simple Agents)

**Best for:**
- Simple single-agent deployments
- Quick prototyping
- Minimal custom logic

**Steps:**
1. Install AgentCore SDK
2. Decorate agent function with `@app.entrypoint`
3. Deploy using agentcore CLI or boto3

### Approach B: Containerized Application (Full Control)

**Best for:**
- Complex agent architectures
- Custom middleware/hooks
- Multiple agents in one service
- Full control over request/response handling

**Steps:**
1. Create Express/Fastify server with required endpoints
2. Build Docker image for `linux/arm64`
3. Push to Amazon ECR
4. Deploy to AgentCore Runtime

**This guide focuses on Approach B** as it provides the most flexibility for TypeScript developers.

---

## Step-by-Step Implementation Guide

### Step 1: Create Express Server with Required Endpoints

Create `src/server.ts`:

```typescript
import express, { Request, Response } from 'express';
import { Agent } from '@strands/agents';
import { BedrockProvider } from '@strands/agents/providers/bedrock';

const app = express();
app.use(express.json());

// Store sessions in memory (use Redis/DynamoDB for production)
const sessions = new Map<string, Agent>();

// Health check endpoint (required by AgentCore)
app.get('/ping', (req: Request, res: Response) => {
  res.status(200).send('OK');
});

// Agent invocation endpoint (required by AgentCore)
app.post('/invocations', async (req: Request, res: Response) => {
  try {
    const { sessionId, input } = req.body;

    // Validate session ID length (33+ characters required)
    if (!sessionId || sessionId.length < 33) {
      return res.status(400).json({
        error: 'Session ID must be at least 33 characters'
      });
    }

    // Get or create agent for this session
    let agent = sessions.get(sessionId);
    if (!agent) {
      agent = new Agent({
        modelProvider: new BedrockProvider({
          model: 'anthropic.claude-sonnet-4-5-v2:0',
          region: 'us-east-1'
        }),
        systemPrompt: 'You are a helpful AI assistant.',
        // Add your custom tools here
      });
      sessions.set(sessionId, agent);
    }

    // Execute agent
    const result = await agent.execute(input);

    // Return response
    res.json({
      sessionId,
      response: result.content,
      metadata: {
        modelUsed: result.modelUsed,
        tokensUsed: result.tokensUsed
      }
    });

  } catch (error) {
    console.error('Agent execution error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Start server on port 8080 (required by AgentCore)
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`AgentCore-compatible server running on port ${PORT}`);
});
```

### Step 2: Create TypeScript Configuration

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### Step 3: Create Package Configuration

Create `package.json`:

```json
{
  "name": "strands-agentcore-typescript",
  "version": "1.0.0",
  "description": "TypeScript Strands Agent for Amazon Bedrock AgentCore",
  "main": "dist/server.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "dev": "tsx watch src/server.ts",
    "docker:build": "docker build --platform linux/arm64 -t strands-agent .",
    "docker:run": "docker run -p 8080:8080 strands-agent"
  },
  "dependencies": {
    "@strands/agents": "latest",
    "@aws-sdk/client-bedrock-runtime": "^3.x",
    "express": "^4.18.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0",
    "@types/node": "^20.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.3.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### Step 4: Create Dockerfile for ARM64

Create `Dockerfile`:

```dockerfile
# Multi-stage build for smaller image size
FROM --platform=linux/arm64 node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Production stage
FROM --platform=linux/arm64 node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --production

# Copy built application
COPY --from=builder /app/dist ./dist

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

# Expose port 8080 (required by AgentCore)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/ping', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start server
CMD ["node", "dist/server.js"]
```

### Step 5: Build and Test Locally

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Test locally (development mode)
npm run dev

# In another terminal, test the endpoints
curl http://localhost:8080/ping

curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-id-12345678901234567890123",
    "input": "Hello, what can you help me with?"
  }'
```

### Step 6: Build Docker Image for ARM64

```bash
# Build for ARM64 architecture (required by AgentCore)
docker build --platform linux/arm64 -t strands-agent:latest .

# Test locally (if on ARM Mac, otherwise use emulation)
docker run -p 8080:8080 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  strands-agent:latest

# Test the containerized app
curl http://localhost:8080/ping
```

### Step 7: Push to Amazon ECR

```bash
# Set variables
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="strands-agentcore-typescript"

# Create ECR repository
aws ecr create-repository \
  --repository-name $ECR_REPO_NAME \
  --region $AWS_REGION

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag image
docker tag strands-agent:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest
```

### Step 8: Deploy to AgentCore Runtime

```bash
# Using AWS CLI (example - adjust based on AgentCore CLI when available)
aws bedrock-agentcore create-agent-runtime \
  --agent-name "typescript-strands-agent" \
  --image-uri "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest" \
  --region $AWS_REGION

# Alternative: Use boto3/SDK in Python deployment script
# Alternative: Use agentcore CLI (when available)
```

**Note**: As of this writing, AgentCore deployment commands may vary. Refer to the latest AWS documentation for the exact deployment CLI/SDK commands.

---

## Environment Variables

Create `.env.example`:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-v2:0
BEDROCK_REGION=us-east-1

# Application Configuration
PORT=8080
LOG_LEVEL=info

# Session Storage (for production)
REDIS_URL=redis://localhost:6379
DYNAMODB_TABLE=agent-sessions
```

---

## Advanced Features

### Session Persistence with DynamoDB

```typescript
import { DynamoDBClient, GetItemCommand, PutItemCommand } from '@aws-sdk/client-dynamodb';

const dynamodb = new DynamoDBClient({ region: 'us-east-1' });

async function getAgentSession(sessionId: string) {
  const result = await dynamodb.send(new GetItemCommand({
    TableName: 'agent-sessions',
    Key: { sessionId: { S: sessionId } }
  }));

  return result.Item ? JSON.parse(result.Item.state.S!) : null;
}

async function saveAgentSession(sessionId: string, state: any) {
  await dynamodb.send(new PutItemCommand({
    TableName: 'agent-sessions',
    Item: {
      sessionId: { S: sessionId },
      state: { S: JSON.stringify(state) },
      lastUpdated: { N: Date.now().toString() }
    }
  }));
}
```

### Streaming Responses

```typescript
app.post('/invocations/stream', async (req: Request, res: Response) => {
  const { sessionId, input } = req.body;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const agent = sessions.get(sessionId) || createNewAgent();

  for await (const chunk of agent.executeStream(input)) {
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
  }

  res.end();
});
```

### Custom Tools Integration

```typescript
import { Tool } from '@strands/agents';

const weatherTool: Tool = {
  name: 'get_weather',
  description: 'Get current weather for a location',
  parameters: {
    type: 'object',
    properties: {
      location: { type: 'string', description: 'City name' }
    },
    required: ['location']
  },
  execute: async ({ location }) => {
    // Call weather API
    const response = await fetch(`https://api.weather.com/v1/${location}`);
    return await response.json();
  }
};

const agent = new Agent({
  modelProvider: new BedrockProvider({ model: 'anthropic.claude-sonnet-4-5-v2:0' }),
  tools: [weatherTool]
});
```

---

## Testing the Deployed Agent

### Test Script

Create `test-agent.sh`:

```bash
#!/bin/bash

# AgentCore endpoint (replace with your actual endpoint)
AGENTCORE_ENDPOINT="https://your-agentcore-endpoint.amazonaws.com"

# Generate a valid session ID (33+ characters)
SESSION_ID="session-$(uuidgen | tr -d '-')-$(date +%s)"

echo "Testing AgentCore deployment..."
echo "Session ID: $SESSION_ID"

# Test health endpoint
echo -e "\n1. Testing /ping endpoint..."
curl -s "$AGENTCORE_ENDPOINT/ping"

# Test agent invocation
echo -e "\n\n2. Testing /invocations endpoint..."
curl -s -X POST "$AGENTCORE_ENDPOINT/invocations" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"input\": \"Hello! What can you help me with today?\"
  }" | jq .

# Test conversation continuity
echo -e "\n\n3. Testing conversation continuity (same session)..."
curl -s -X POST "$AGENTCORE_ENDPOINT/invocations" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"input\": \"What did I just ask you?\"
  }" | jq .
```

### Load Testing

```bash
# Install artillery for load testing
npm install -g artillery

# Create artillery config
cat > load-test.yml <<EOF
config:
  target: "https://your-agentcore-endpoint.amazonaws.com"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - flow:
      - post:
          url: "/invocations"
          json:
            sessionId: "load-test-{{ \$randomString() }}-{{ \$randomNumber() }}"
            input: "Hello, this is a load test"
EOF

# Run load test
artillery run load-test.yml
```

---

## Troubleshooting

### Common Issues

#### 1. Session ID Too Short

**Error**: `Session ID must be at least 33 characters`

**Solution**:
```typescript
// Generate valid session ID
const sessionId = `session-${crypto.randomUUID()}-${Date.now()}`;
console.log(sessionId.length); // Should be 33+
```

#### 2. ARM64 Build Fails on x86 Machine

**Error**: `exec format error` or architecture mismatch

**Solution**:
```bash
# Enable Docker BuildKit
export DOCKER_BUILDKIT=1

# Build with explicit platform
docker buildx build --platform linux/arm64 -t strands-agent .

# Or use Docker Desktop with ARM emulation enabled
```

#### 3. Port 8080 Already in Use

**Error**: `EADDRINUSE: address already in use :::8080`

**Solution**:
```bash
# Find process using port 8080
lsof -ti:8080

# Kill the process
kill -9 $(lsof -ti:8080)

# Or use different port locally (but AgentCore requires 8080)
PORT=3000 npm run dev
```

#### 4. AWS Credentials Not Found

**Error**: `Unable to locate credentials`

**Solution**:
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1

# Or use IAM role (recommended for production)
```

#### 5. Bedrock Access Denied

**Error**: `AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel`

**Solution**:
```bash
# Ensure IAM role has Bedrock permissions
aws iam attach-role-policy \
  --role-name your-agentcore-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

---

## Comparison: When to Use Each Deployment Option

### AgentCore vs. Lambda vs. Fargate

| Use Case | Recommended | Why |
|----------|-------------|-----|
| **Simple API agent** | AgentCore or Lambda | Minimal setup, serverless |
| **Streaming responses** | AgentCore or Fargate | Lambda doesn't support streaming |
| **Long-running agents (>15 min)** | AgentCore or Fargate | Lambda has 15-minute timeout |
| **Multi-agent orchestration** | AgentCore | Built-in A2A protocol support |
| **WebSocket real-time chat** | Fargate | Full control over connections |
| **Cost optimization (low traffic)** | Lambda | Pay only per invocation |
| **Cost optimization (high traffic)** | Fargate or AgentCore | More predictable pricing |
| **Zero infrastructure** | AgentCore | Fully managed, no servers |
| **Session isolation** | AgentCore | Built-in microVM isolation |
| **Custom middleware/hooks** | Fargate | Full control over Express app |

### Decision Matrix

```
Start Here: Do you need streaming?
├─ No → Lambda (simplest, cheapest for low traffic)
└─ Yes → Do you need custom infrastructure?
    ├─ No → AgentCore (managed, zero ops)
    └─ Yes → Fargate (full control)
```

---

## Production Checklist

### Security

- [ ] Use IAM roles instead of access keys
- [ ] Enable encryption at rest and in transit
- [ ] Implement request validation and sanitization
- [ ] Set up VPC for network isolation
- [ ] Enable CloudWatch Logs for monitoring
- [ ] Implement rate limiting
- [ ] Use AWS Secrets Manager for sensitive data

### Monitoring

- [ ] Set up CloudWatch metrics
- [ ] Configure CloudWatch alarms
- [ ] Implement structured logging
- [ ] Track agent performance metrics
- [ ] Monitor token usage and costs
- [ ] Set up distributed tracing (X-Ray)

### Reliability

- [ ] Implement health checks
- [ ] Configure auto-scaling policies
- [ ] Set up multi-region deployment (if needed)
- [ ] Implement circuit breakers
- [ ] Configure retry logic with exponential backoff
- [ ] Test disaster recovery procedures

### Performance

- [ ] Optimize Docker image size
- [ ] Use connection pooling for external services
- [ ] Implement caching where appropriate
- [ ] Configure appropriate timeout values
- [ ] Load test before production launch
- [ ] Monitor and optimize cold start times

---

## Cost Estimation

### AgentCore (Preview - FREE until Sept 2025)

After preview, pricing will likely be based on:
- Agent runtime hours
- Number of invocations
- Data transfer

### Alternative: Fargate (Current Pricing)

**Example calculation for moderate traffic:**
- Task: 0.5 vCPU, 1 GB RAM
- 2 tasks running 24/7
- Cost: ~$30-40/month

**Example calculation for high traffic:**
- Task: 1 vCPU, 2 GB RAM
- 5 tasks running 24/7
- Cost: ~$150-200/month

### Alternative: Lambda (Current Pricing)

**Example calculation:**
- 1 million requests/month
- 512 MB memory, 3 second duration
- Cost: ~$20-30/month

---

## Next Steps

### Related Documentation

1. **TypeScript SDK Tutorials** (Planned)
   - `typescript/01-tutorials/01-first-agent/`
   - `typescript/01-tutorials/02-custom-tools/`
   - `typescript/01-tutorials/04-streaming/`

2. **Deployment Tutorials**
   - `01-tutorials/03-deployment/01-lambda-deployment/` (Python)
   - `01-tutorials/03-deployment/02-fargate-deployment/` (Python)

3. **AgentCore Tutorials** (Planned)
   - Tutorial F15: Code Execution and Interpretation
   - Tutorial F18: Production Deployment Patterns
   - Tutorial F11: Agent-to-Agent (A2A) Protocol

### Additional Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands Agents TypeScript SDK](https://strandsagents.com/latest/documentation/)
- [AWS SDK for JavaScript v3](https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/)
- [Express.js Documentation](https://expressjs.com/)

### Community & Support

- [AWS re:Post - Bedrock AgentCore](https://repost.aws/tags/bedrock-agentcore)
- [Strands Agents GitHub](https://github.com/aws/strands-agents)
- [AWS Bedrock Community](https://community.aws/bedrock)

---

## Example Project Structure

```
strands-agentcore-typescript/
├── src/
│   ├── server.ts                 # Main Express server
│   ├── agent/
│   │   ├── config.ts            # Agent configuration
│   │   ├── tools.ts             # Custom tools
│   │   └── prompts.ts           # System prompts
│   ├── middleware/
│   │   ├── auth.ts              # Authentication
│   │   ├── validation.ts        # Request validation
│   │   └── logging.ts           # Structured logging
│   └── utils/
│       ├── session.ts           # Session management
│       └── errors.ts            # Error handling
├── tests/
│   ├── server.test.ts
│   └── agent.test.ts
├── Dockerfile
├── docker-compose.yml           # For local testing
├── package.json
├── tsconfig.json
├── .env.example
├── .dockerignore
└── README.md
```

---

## Conclusion

Amazon Bedrock AgentCore Runtime provides a powerful, serverless platform for deploying TypeScript-based Strands agents with minimal infrastructure overhead. With built-in session isolation, auto-scaling, and native support for agent protocols, it's an excellent choice for production deployments.

**Key Takeaways:**
- ✅ TypeScript is fully supported via containerization
- ✅ Express/Fastify servers work seamlessly
- ✅ Free during preview period (until Sept 2025)
- ✅ Minimal setup compared to Fargate/ECS
- ✅ Built-in features (session isolation, A2A, MCP)

**Start deploying today and take advantage of the free preview!**

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Feedback**: Submit issues or improvements to the repository
