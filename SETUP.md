# Setup & Run Guide — AWS Bedrock

---

## Part 1 — Run Locally

### Step 1 — Prerequisites

```bash
# Install Python dependencies
cd multi_agent_aws_sol1
pip install -r requirements.txt

# Install ADK CLI (if not already included)
pip install google-adk
```

### Step 2 — Configure AWS credentials

**Option A — IAM role (production / recommended)**
No credentials needed — attach the IAM role to your EC2/ECS/EKS workload.

**Option B — AWS CLI (local development)**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)
```

**Option C — Environment variables**
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

### Step 3 — Enable Bedrock model access

```
AWS Console → Amazon Bedrock → Model access → Request access
Enable: Anthropic Claude models (claude-sonnet-4-5, claude-opus-4-5)
```

### Step 4 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
AWS_REGION=us-east-1
SUPERVISOR_MODEL=bedrock/anthropic.claude-sonnet-4-5
RAG_MODEL=bedrock/anthropic.claude-sonnet-4-5
ACTION_MODEL=bedrock/anthropic.claude-sonnet-4-5
POLICY_MODEL=bedrock/anthropic.claude-opus-4-5
KNOWLEDGE_BASE_ID=your-kb-id      # from Bedrock → Knowledge Bases
GUARDRAIL_ID=your-guardrail-id    # from Bedrock → Guardrails (optional)
```

### Step 5 — Run locally (3 options)

**Option A — Web UI (recommended)**
```bash
adk web multi_agent_aws_sol1/
```
Opens `http://localhost:8000` — interactive chat UI with agent routing,
tool calls, and Bedrock Knowledge Base retrieval visible in real time.

**Option B — CLI interactive**
```bash
adk run multi_agent_aws_sol1/

# Example queries:
# > What is the policy on remote access to production?
# > Create a P2 ticket: VPN is broken for payments team.
```

**Option C — Direct Python**
```bash
python multi_agent_aws_sol1/main.py
```

---

## Part 2 — Deploy to AWS (EKS / ECS / Fargate)

### Step 1 — Enable required services

```bash
# Bedrock is regional — ensure it is available in your region
aws bedrock list-foundation-models --region us-east-1

# Create a Bedrock Knowledge Base (if not already created)
# AWS Console → Amazon Bedrock → Knowledge Bases → Create
```

### Step 2 — Create IAM role for the agent service

```bash
# Minimal permissions for the agent service account
aws iam create-policy \
  --policy-name enterprise-agent-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Retrieve",
          "bedrock:ApplyGuardrail"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": ["secretsmanager:GetSecretValue"],
        "Resource": "arn:aws:secretsmanager:*:*:secret:enterprise-agent/*"
      },
      {
        "Effect": "Allow",
        "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": "*"
      }
    ]
  }'
```

### Step 3 — Build and push container

```bash
# Build
docker build -t enterprise-agent-aws .

# Push to ECR
aws ecr create-repository --repository-name enterprise-agent-aws --region us-east-1
docker tag enterprise-agent-aws:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/enterprise-agent-aws:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/enterprise-agent-aws:latest
```

### Step 4 — Deploy on ECS/Fargate

```bash
# Create ECS task definition with the IAM role and container image
# AWS Console → ECS → Task Definitions → Create
# Or use the AWS CDK / Terraform for infrastructure as code
```

### Step 5 — (Optional) ADOT for CloudWatch traces

```bash
# Add ADOT sidecar container to your ECS task definition
# Image: public.ecr.aws/aws-observability/aws-otel-collector:latest
# This receives OTLP traces from the app and forwards to CloudWatch / X-Ray
```

---

## Quick Reference

| Task | Command |
|---|---|
| Authenticate (local) | `aws configure` |
| Run web UI | `adk web multi_agent_aws_sol1/` |
| Run CLI | `adk run multi_agent_aws_sol1/` |
| Run Python directly | `python multi_agent_aws_sol1/main.py` |
| View traces | AWS Console → CloudWatch → X-Ray traces |
| View logs | AWS Console → CloudWatch → Log Groups |
| Test Bedrock access | `aws bedrock list-foundation-models --region us-east-1` |

---

## Switching Bedrock Models

Update `SUPERVISOR_MODEL` / `RAG_MODEL` / `POLICY_MODEL` in `.env`:

| Model | LiteLLM string |
|---|---|
| Claude Sonnet 4.5 | `bedrock/anthropic.claude-sonnet-4-5` |
| Claude Opus 4.5 | `bedrock/anthropic.claude-opus-4-5` |
| Claude Haiku 4.5 | `bedrock/anthropic.claude-haiku-4-5-20251001` |
| Amazon Nova Pro | `bedrock/amazon.nova-pro-v1:0` |
| Llama 3.1 70B | `bedrock/meta.llama3-1-70b-instruct-v1:0` |

---

## Troubleshooting

**`AccessDeniedException` on Bedrock call**
```
AWS Console → Bedrock → Model access → confirm model is enabled in your region
```

**`NoCredentialsError`**
```bash
aws configure   # or set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars
```

**Knowledge Base returns no results**
```
AWS Console → Bedrock → Knowledge Bases → confirm KB is synced (status = Available)
```

**`adk web` not found**
```bash
pip install google-adk --upgrade
```
