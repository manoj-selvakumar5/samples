# SageMaker Notebook for Strands Agent Deployment to AgentCore

This CloudFormation template creates a SageMaker notebook instance with the necessary IAM permissions to deploy Strands agents to Amazon Bedrock AgentCore Runtime using the starter toolkit.

## Architecture

```
+-------------------------------------------------------------------------+
|                         SageMaker Notebook                               |
|  +-------------------------------------------------------------------+  |
|  |  pip install bedrock-agentcore-starter-toolkit strands-agents     |  |
|  |  agentcore create  ->  agentcore dev  ->  agentcore launch        |  |
|  +-------------------------------------------------------------------+  |
|                                    |                                     |
|                     SageMaker Execution Role                            |
+------------------------------------+------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                           |                           |
         v                           v                           v
   +----------+              +--------------+            +-------------+
   |   IAM    |              |  CodeBuild   |            |     ECR     |
   | (Roles)  |              | (Build Img)  |            |  (Images)   |
   +----------+              +--------------+            +-------------+
         |                           |                           |
         +---------------------------+---------------------------+
                                     v
                       +------------------------+
                       |   AgentCore Runtime    |
                       |  +------------------+  |
                       |  |   Strands Agent  |  |
                       |  +------------------+  |
                       +------------------------+
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Access to Amazon Bedrock models (e.g., Claude Sonnet)

## Deployment

### Deploy the CloudFormation Stack

```bash
aws cloudformation create-stack \
  --stack-name strands-agentcore-notebook \
  --template-body file://sagemaker-agentcore-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### Wait for Stack Creation

```bash
aws cloudformation wait stack-create-complete \
  --stack-name strands-agentcore-notebook
```

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name strands-agentcore-notebook \
  --query 'Stacks[0].Outputs'
```

## Using the Notebook

1. **Open SageMaker Console** - Navigate to Notebooks and open Jupyter

2. **Install Dependencies**:
   ```bash
   pip install bedrock-agentcore-starter-toolkit strands-agents bedrock-agentcore
   ```

3. **Create Agent Project**:
   ```bash
   agentcore create
   # Choose: Strands Agents framework
   # Enter: Your project name
   ```

4. **Test Locally** (optional):
   ```bash
   agentcore dev
   # In another terminal:
   agentcore invoke --dev "Hello!"
   ```

5. **Deploy to AgentCore Runtime**:
   ```bash
   agentcore launch
   ```

6. **Invoke Deployed Agent**:
   ```bash
   agentcore invoke '{"prompt": "Tell me a joke"}'
   ```

## Starter Toolkit Workflow

```
agentcore create     -> Scaffold a Strands agent project
agentcore dev        -> Start local development server
agentcore launch     -> Deploy to AgentCore Runtime
                        |
                        +-> Creates IAM execution role (if not pre-created)
                        +-> Creates CodeBuild project
                        +-> Builds container image
                        +-> Pushes to ECR
                        +-> Creates AgentCore Runtime

agentcore invoke     -> Test the deployed agent
agentcore cleanup    -> Delete the deployed agent
```

## Permissions Explained

### SageMaker Execution Role

| Permission | Why Needed |
|------------|------------|
| `BedrockAgentCoreFullAccess` | Managed policy to create/manage/invoke AgentCore runtimes |
| `iam:CreateRole`, `iam:PutRolePolicy` | Starter toolkit auto-creates agent execution roles |
| `iam:PassRole` | Assign execution role to AgentCore runtime |
| `codebuild:CreateProject`, `codebuild:StartBuild` | Build container images without local Docker |
| `ecr:CreateRepository`, `ecr:PutImage` | Store container images |
| `s3:CreateBucket`, `s3:PutObject` | Store build artifacts |
| `logs:GetLogEvents` | View build and runtime logs |
| `bedrock:InvokeModel` | Test agents locally in notebook |

### Agent Execution Role (Auto-Created by Toolkit)

The starter toolkit automatically creates an execution role for the deployed agent with:

| Permission | Purpose |
|------------|---------|
| `ecr:BatchGetImage` | Pull container image at runtime |
| `logs:CreateLogStream`, `logs:PutLogEvents` | Write runtime logs |
| `xray:PutTraceSegments` | Distributed tracing |
| `cloudwatch:PutMetricData` | Publish metrics |
| `bedrock-agentcore:GetWorkloadAccessToken*` | Workload identity |
| `bedrock:InvokeModel` | Call Bedrock models |

## Using Pre-Created Execution Role

If you want to use the pre-created agent execution role instead of letting the toolkit create one:

```bash
# Get the role ARN from stack outputs
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name strands-agentcore-notebook \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentExecutionRoleArn`].OutputValue' \
  --output text)

# Use with agentcore launch (check toolkit docs for exact flag)
agentcore launch --execution-role-arn $ROLE_ARN
```

## Cleanup

```bash
# Delete the deployed agent
agentcore cleanup

# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name strands-agentcore-notebook

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name strands-agentcore-notebook
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `AccessDenied` during `agentcore launch` | Check SageMaker role has IAM and CodeBuild permissions |
| Build fails | Check CodeBuild logs: `/aws/codebuild/bedrock-agentcore-*` |
| Agent invocation fails | Check runtime logs: `/aws/bedrock-agentcore/runtimes/*` |
| Model access denied | Enable Bedrock model access in the console |
| Role not found | Ensure role names match `*BedrockAgentCore*` pattern |

## CloudWatch Log Groups

| Log Group | Purpose |
|-----------|---------|
| `/aws/codebuild/bedrock-agentcore-*` | Container build logs |
| `/aws/bedrock-agentcore/runtimes/*` | Agent runtime logs |

## Template Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NotebookInstanceName` | `strands-agentcore-notebook` | SageMaker notebook instance name |
| `InstanceType` | `ml.t3.medium` | Notebook instance type |

## References

- [Amazon Bedrock AgentCore Developer Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [Starter Toolkit Permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html#runtime-permissions-starter-toolkit)
- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/docs/)
- [AgentCore Starter Toolkit GitHub](https://github.com/aws/bedrock-agentcore-starter-toolkit)
