# Strands Agents Workshop - CloudFormation Templates

This folder contains CloudFormation templates for deploying Amazon SageMaker Studio environments for the Strands Agents workshop.

## Files

| File | Description |
|------|-------------|
| `original_strands_workshop_studio.yaml` | Base template for tutorials in `01-tutorials/01-fundamentals/` and `01-tutorials/02-advanced/` |
| `strands_workshop_studio.yaml` | Extended template with AgentCore permissions for `01-tutorials/03-deployment/03-agentcore-deployment/` |
| `original_iam_policy.json` | Base IAM policy template for WSParticipantRole |
| `iam_policy.json` | Extended policy with AgentCore permissions for deployment tutorials |

## Template Overview

The CloudFormation template creates a complete SageMaker Studio environment:

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFormation Stack                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Lambda Functions│    │     SageMaker Studio Domain     │ │
│  │  - VPC Finder   │    │  ┌─────────────────────────────┐│ │
│  │  - Lifecycle    │───▶│  │      User Profile          ││ │
│  │    Config       │    │  │  ┌─────────────────────────┐││ │
│  └─────────────────┘    │  │  │   JupyterLab Space     │││ │
│                         │  │  │   (100GB EBS)          │││ │
│  ┌─────────────────┐    │  │  └─────────────────────────┘││ │
│  │   IAM Roles     │    │  └─────────────────────────────┘│ │
│  │  - SageMaker    │───▶│     Docker Access: ENABLED      │ │
│  │  - Lambda       │    └─────────────────────────────────┘ │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `UserProfileName` | `strandsuser` | SageMaker user profile name |
| `DomainName` | `strands-agents-workshop` | SageMaker Studio domain name |
| `SpaceName` | `strands-workshop-space` | JupyterLab space name |

## Resources Created

### 1. IAM Roles

#### LambdaExecutionRole
Helper role for Lambda functions that find VPC info and configure lifecycle scripts.

#### SageMakerExecutionRole
Main execution role for SageMaker Studio with policies for all workshop tutorials.

**Trust Relationships:**
- `sagemaker.amazonaws.com`
- `bedrock.amazonaws.com`
- `bedrock-agentcore.amazonaws.com` *(only in strands_workshop_studio.yaml)*

### 2. Lambda Functions

| Function | Purpose |
|----------|---------|
| `DefaultVpcLambda` | Finds default VPC and subnets for Studio deployment |
| `LifeCycleConfigLambda` | Clones workshop notebooks on JupyterLab startup |

### 3. SageMaker Resources

| Resource | Description |
|----------|-------------|
| `StudioDomain` | SageMaker Studio domain with Docker access enabled |
| `UserProfile` | User profile linked to execution role |
| `JupyterLabSpace` | Private JupyterLab space with 100GB storage |

## SageMaker Execution Role Policies

### Managed Policies

| Policy | Purpose |
|--------|---------|
| `AmazonSageMakerFullAccess` | SageMaker operations |
| `AWSCloudFormationReadOnlyAccess` | View CloudFormation stacks |
| `AmazonS3ReadOnlyAccess` | Read S3 buckets |
| `AmazonBedrockReadOnly` | List Bedrock models |
| `AmazonBedrockLimitedAccess` | Invoke Bedrock models |

### Inline Policies (Base Template)

| Policy Name | Actions | Tutorials Supported |
|-------------|---------|---------------------|
| `s3-access` | Create/Read/Write/Delete buckets and objects | All tutorials |
| `s3-create-bucket-access` | Create S3 buckets | Knowledge Base tutorials |
| `iam-access` | Create/manage IAM roles and policies | All tutorials |
| `bedrock-kb-access` | Knowledge Base CRUD, Retrieve, InvokeModel | 03-connecting-with-aws-services |
| `bedrock-agents-access` | Agent CRUD, Invoke, Collaborators | Advanced agent tutorials |
| `bedrock-guardrail-access` | Guardrail CRUD | Guardrail tutorials |
| `bedrock-deny` | Deny model customization jobs | Security restriction |
| `aoss-access` | OpenSearch Serverless collections/policies | Knowledge Base tutorials |
| `aoss-access-api` | OpenSearch Serverless API access | Knowledge Base tutorials |
| `lambda-access` | Create/invoke Lambda functions | Agent action groups |
| `dynamodb-access` | Table CRUD, item operations | Restaurant assistant |
| `cfn-access` | CloudFormation stack operations | CDK deployments |
| `ssm-access` | Parameter Store operations | Configuration storage |
| `ecr-access` | ECR push/delete | Container deployments |
| `sns-access` | SNS full access | Notifications |

---

## AgentCore Additions (strands_workshop_studio.yaml)

The extended template adds permissions for the **03-agentcore-deployment** tutorial.

### Trust Policy Addition

```yaml
- Effect: Allow
  Principal:
    Service:
      - bedrock-agentcore.amazonaws.com
  Action:
    - sts:AssumeRole
    - sts:TagSession
```

### Additional Inline Policies

Based on [AWS AgentCore IAM Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html):

| Policy Name | Actions | Resource Scope |
|-------------|---------|----------------|
| `bedrock-agentcore-access` | 12 specific runtime actions (see below) | `arn:aws:bedrock-agentcore:*:*:*` |
| `agentcore-codebuild-access` | StartBuild, CreateProject, BatchGetBuilds | `project/bedrock-agentcore-*`, `build/bedrock-agentcore-*` |
| `agentcore-iam-access` | CreateRole, DeleteRole, PassRole, etc. | `role/*BedrockAgentCore*` |
| `agentcore-ecr-access` | CreateRepository, PutImage, GetAuthorizationToken | `repository/bedrock-agentcore-*` |
| `agentcore-logs-access` | GetLogEvents, DescribeLogGroups | `/aws/bedrock-agentcore/*` |
| `agentcore-s3-access` | GetObject, PutObject, CreateBucket | `bedrock-agentcore-*` |
| `agentcore-xray-access` | PutTraceSegments, GetSamplingRules, UpdateTraceSegmentDestination | `*` |
| `agentcore-observability-logs` | PutDeliverySource, CreateDelivery, etc. | `*` |
| `agentcore-application-signals` | StartDiscovery | `*` |

#### Understanding CodeBuild Resource ARN Patterns

The `agentcore-codebuild-access` policy uses ARN patterns to scope permissions:

```
arn:aws:codebuild:*:*:project/bedrock-agentcore-*
     │      │     │ │    │            │
     │      │     │ │    │            └─ Project name prefix
     │      │     │ │    └─ Resource type
     │      │     │ └─ Account ID (* = any)
     │      │     └─ Region (* = any)
     │      └─ AWS service
     └─ AWS partition
```

| ARN Pattern | Purpose |
|-------------|---------|
| `project/bedrock-agentcore-*` | Create/update/delete CodeBuild **projects** named `bedrock-agentcore-<agent_name>` |
| `build/bedrock-agentcore-*` | Start and monitor **builds** from those projects |

When `runtime.launch()` is called, the starter toolkit:
1. Creates a CodeBuild project named `bedrock-agentcore-<your_agent_name>`
2. Starts a build to create your Docker image
3. Pushes the image to ECR

This scoping ensures workshop participants can only access CodeBuild resources with the `bedrock-agentcore-` prefix.

### Security Notes

These policies follow **least privilege** principles:
- Resources are scoped to `bedrock-agentcore-*` prefixes
- Only actions required by the starter toolkit are included
- Suitable for workshops with 1000s of participants

---

## Deployment

### Prerequisites
- AWS CLI configured with appropriate credentials
- Permissions to create IAM roles, Lambda functions, and SageMaker resources

### Deploy Base Template
```bash
aws cloudformation create-stack \
  --stack-name strands-workshop \
  --template-body file://original_strands_workshop_studio.yaml \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### Deploy with AgentCore Support
```bash
aws cloudformation create-stack \
  --stack-name strands-workshop \
  --template-body file://strands_workshop_studio.yaml \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### Supported Regions
- `us-east-1`
- `us-west-2`

### Validate Template
```bash
aws cloudformation validate-template \
  --template-body file://strands_workshop_studio.yaml
```

---

## Lifecycle Configuration

On JupyterLab startup, the lifecycle script automatically clones:
```bash
git clone --depth 2 --filter=blob:none --no-checkout https://github.com/strands-agents/samples.git
cd samples
git checkout main -- 01-tutorials/ 02-samples/05-personal-assistant/ 02-samples/01-restaurant-assistant/
```

---

## Cleanup

```bash
aws cloudformation delete-stack --stack-name strands-workshop --region us-east-1
```

**Note:** Delete any resources created during tutorials (S3 buckets, DynamoDB tables, Knowledge Bases) before deleting the stack.

---

## Changelog

### 2026-01-03: Added Workload Identity and Cleanup Permissions for AgentCore

#### Fix 1: Workload Identity Permissions

**Issue:** When running `agentcore_runtime.launch()` in the AgentCore deployment tutorial, workshop participants encountered:

```
AccessDeniedException: bedrock-agentcore:CreateWorkloadIdentity on resource:
arn:aws:bedrock-agentcore:*:*:workload-identity-directory/default/workload-identity/*
```

**Root Cause:** The `bedrock-agentcore-access` policy only included runtime lifecycle actions but was missing workload identity actions. When `CreateAgentRuntime` is called, AWS AgentCore automatically creates a workload identity for secure credential management. This requires explicit permissions not included in the original policy.

**What was added:**

1. **Workload Identity Actions** - Added to existing `bedrock-agentcore-access` policy:
   - `CreateWorkloadIdentity` - Creates workload identity during `CreateAgentRuntime`
   - `GetWorkloadIdentity` - Retrieves workload identity status
   - `DeleteWorkloadIdentity` - Cleans up identity during `DeleteAgentRuntime`
   - `ListWorkloadIdentities` - Lists existing workload identities

2. **Service-Linked Role Permission** - New `agentcore-service-linked-role` policy:
   - `iam:CreateServiceLinkedRole` for `AWSServiceRoleForBedrockAgentCoreRuntimeIdentity`
   - Required on first AgentCore deployment in an account
   - AWS uses this service-linked role to manage runtime identity federation

**Why Workload Identity?**
- Workload identities allow AgentCore to securely provide temporary credentials to your deployed agent
- The agent can then access AWS services (like Bedrock models) without embedding long-term credentials
- This is the recommended pattern for production agent deployments

#### Fix 2: Cleanup Permissions

**Issue:** The tutorial uses `agentcore destroy --force --delete-ecr-repo` for cleanup, but the required permissions were missing.

**What was added:**

1. **CodeBuild DeleteProject** - Added to `agentcore-codebuild-access` policy:
   - `codebuild:DeleteProject` - Required by `agentcore destroy` to remove CodeBuild projects

2. **ECR Cleanup Actions** - Added to `agentcore-ecr-access` policy:
   - `ecr:DeleteRepository` - Required for `--delete-ecr-repo` flag
   - `ecr:BatchDeleteImage` - Required to delete images before repository deletion

#### Fix 3: Observability Permissions

**Issue:** After successful deployment, observability features failed with:
- `xray:UpdateTraceSegmentDestination` - Transaction Search configuration failed
- `logs:PutDeliverySource` - Failed to enable observability for runtime

**What was added:**

1. **X-Ray Transaction Search** - Added to `agentcore-xray-access` policy:
   - `xray:UpdateTraceSegmentDestination` - Configure trace segment destinations
   - `xray:GetTraceSegmentDestination` - Read trace segment destinations
   - `xray:GetIndexingRules` - Read indexing rules
   - `xray:UpdateIndexingRule` - Update indexing rules

2. **CloudWatch Logs Delivery** - New `agentcore-observability-logs` policy:
   - `logs:PutDeliverySource`, `logs:PutDeliveryDestination`, `logs:CreateDelivery` - Create observability pipelines
   - `logs:DeleteDelivery*` - Cleanup delivery resources
   - `logs:GetDelivery*`, `logs:DescribeDeliveries*` - Read delivery configurations

**Reference:**
- https://docs.aws.amazon.com/aws-managed-policy/latest/reference/BedrockAgentCoreFullAccess.html

#### Fix 4: IAM Policy for WSParticipantRole

**Issue:** Workshop participants using WSParticipantRole encountered `AccessDeniedException` for `bedrock-agentcore:ListAgentRuntimes` when running the AgentCore deployment tutorial.

**Root Cause:** The `original_iam_policy.json` (used for WSParticipantRole) has `bedrock:*` permissions but NO `bedrock-agentcore:*` permissions. These are separate service namespaces in AWS IAM.

**File Created:** `iam_policy.json`

**What was added:**

New `BedrockAgentCoreAccess` statement:
- Action: `bedrock-agentcore:*` (wildcard used due to IAM policy size limit of 6144 characters)
- Resource: `arn:aws:bedrock-agentcore:*:*:*`

#### Fix 5: Vended Log Delivery and Application Signals Permissions

**Issue:** After deploying an agent, observability setup failed with:
- `AccessDeniedException` for `bedrock-agentcore:AllowVendedLogDeliveryForResource`
- `AccessDeniedException` for `application-signals:StartDiscovery`

**Root Cause:** The `bedrock-agentcore-access` policy listed specific runtime actions but was missing the `AllowVendedLogDeliveryForResource` action. Additionally, Application Signals (for Transaction Search) is a separate AWS service requiring its own permissions.

**What was added:**

1. **Vended Log Delivery** - Added to `bedrock-agentcore-access` policy:
   - `bedrock-agentcore:AllowVendedLogDeliveryForResource` - Required for AgentCore to deliver logs and traces to CloudWatch

2. **Application Signals** - New `agentcore-application-signals` policy:
   - `application-signals:StartDiscovery` - Required for Transaction Search observability feature

---

### 2026-01-02: Added Amazon Bedrock AgentCore Support

**File Created:** `strands_workshop_studio.yaml`

**Why:** The base template (`original_strands_workshop_studio.yaml`) does not include permissions required for the `01-tutorials/03-deployment/03-agentcore-deployment/` tutorial. Workshop participants attempting to deploy agents using the Amazon Bedrock AgentCore starter toolkit would encounter permission errors.

**What was added:**

1. **Trust Policy Update** - Added `bedrock-agentcore.amazonaws.com` as a trusted service principal with `sts:AssumeRole` and `sts:TagSession` actions. This allows AgentCore to assume the SageMaker execution role when running deployed agents.

2. **10 New Inline Policies** - Based on [AWS AgentCore IAM Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html):

   | Policy | Why Needed |
   |--------|------------|
   | `bedrock-agentcore-access` | Runtime lifecycle actions + workload identity + vended log delivery |
   | `agentcore-codebuild-access` | Starter toolkit uses CodeBuild to build Docker images for agent deployment |
   | `agentcore-iam-access` | Toolkit creates execution roles for deployed agents (scoped to `*BedrockAgentCore*` roles) |
   | `agentcore-ecr-access` | Push agent container images to ECR repositories (scoped to `bedrock-agentcore-*`) |
   | `agentcore-logs-access` | View runtime logs in CloudWatch for debugging deployed agents |
   | `agentcore-s3-access` | Toolkit uses S3 buckets for agent artifacts (scoped to `bedrock-agentcore-*`) |
   | `agentcore-xray-access` | Enable distributed tracing and Transaction Search for observability |
   | `agentcore-service-linked-role` | Create service-linked role for runtime identity management |
   | `agentcore-observability-logs` | CloudWatch Logs delivery for observability pipelines |
   | `agentcore-application-signals` | Application Signals for Transaction Search feature |

   **AgentCore Runtime Actions (17 total):**
   - Control plane: `CreateAgentRuntime`, `CreateAgentRuntimeEndpoint`, `GetAgentRuntime`, `GetAgentRuntimeEndpoint`, `DeleteAgentRuntime`, `DeleteAgentRuntimeEndpoint`, `ListAgentRuntimes`, `ListAgentRuntimeEndpoints`, `ListAgentRuntimeVersions`, `UpdateAgentRuntime`, `UpdateAgentRuntimeEndpoint`
   - Data plane: `InvokeAgentRuntime`
   - Workload identity: `CreateWorkloadIdentity`, `GetWorkloadIdentity`, `DeleteWorkloadIdentity`, `ListWorkloadIdentities`
   - Observability: `AllowVendedLogDeliveryForResource`

**Security Considerations:**
- All policies follow **least privilege** principles
- Resources are scoped to `bedrock-agentcore-*` prefixes where possible
- AgentCore policy uses 17 specific actions instead of `bedrock-agentcore:*` wildcard
- Avoided using the broad `BedrockAgentCoreFullAccess` managed policy which includes unnecessary Secrets Manager, KMS, and Lambda permissions
- Suitable for workshops with 1000s of participants

**Reference:** Permissions derived from AWS documentation at:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html
- https://docs.aws.amazon.com/aws-managed-policy/latest/reference/BedrockAgentCoreFullAccess.html
