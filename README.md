# Multi-Agent Enterprise Template — Google ADK + AWS Bedrock

Enterprise-ready multi-agent template using Google ADK as the orchestration framework
and Amazon Bedrock as the AI and knowledge backend.

**Author:** Rohid Dev · github.com/rohiddev

---

## Architecture

```
User Request
    ↓
SupervisorAgent (Claude on Bedrock via LiteLLM)
    ├── RAGAgent        — Amazon Bedrock Knowledge Bases
    ├── ActionAgent     — enterprise system actions (tickets, APIs)
    └── PolicyAgent     — Bedrock Guardrails + IAM policy checks

Knowledge Layer
    └── Bedrock Knowledge Bases
            <- S3 / SharePoint / Confluence / OneDrive / web

Security
    ├── IAM roles + least-privilege policies
    ├── Bedrock Guardrails (blocked topics, PII, grounding)
    ├── AWS Secrets Manager
    └── PrivateLink / VPC endpoints for Bedrock

Observability
    ├── OpenTelemetry -> ADOT -> CloudWatch / X-Ray
    └── CloudWatch Logs (structured)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for a detailed, plain-English walkthrough with annotated diagrams.

---

## Quickstart

```bash
# 1. Install dependencies (Python 3.11+ required)
pip install -r requirements.txt

# 2. Configure AWS credentials
aws configure

# 3. Enable Bedrock model access
# AWS Console -> Bedrock -> Model access -> enable Claude models

# 4. Configure environment
cp .env.example .env
# Edit .env — set KNOWLEDGE_BASE_ID, GUARDRAIL_ID (optional)

# 5. Run
python main.py
```

---

## Folder Structure

```
multi_agent_aws_sol1/
├── main.py                      # Entry point — startup validation, wires everything together
├── agent.py                     # ADK CLI entry point (adk run / adk web)
├── config.py                    # Centralized config with fail-fast validation
├── requirements.txt
├── pyproject.toml               # Python version pin (>=3.11), dev dependencies
├── .env.example
├── ARCHITECTURE.md              # Detailed plain-English architecture diagrams
├── agents/
│   ├── supervisor.py            # Supervisor — routes to specialist agents
│   ├── rag_agent.py             # RAG agent — Bedrock Knowledge Bases
│   ├── action_agent.py          # Action agent — tickets, APIs
│   └── policy_agent.py          # Policy agent — Guardrails + IAM
├── retrieval/
│   └── retrieval.py             # Bedrock Knowledge Bases via boto3
├── tools/
│   └── enterprise_tools.py      # All tool definitions — guardrail-checked, error-handled
├── observability/
│   └── telemetry.py             # Idempotent OpenTelemetry -> ADOT -> CloudWatch / X-Ray
└── security/
    └── aws_security.py          # IAM identity validation, Secrets Manager, Guardrails
```

---

## GCP vs AWS — Side by Side

| Component | GCP (multi_agent_gcp_sol1) | AWS (multi_agent_aws_sol1) |
|---|---|---|
| Agent framework | Google ADK | Google ADK |
| Model | Gemini (native) | Claude on Bedrock (LiteLLM) |
| RAG | Agent Search / RAG Engine / Vector Search | Bedrock Knowledge Bases |
| Content safety | Policy Agent + IAM | Bedrock Guardrails + IAM |
| Secrets | Secret Manager | Secrets Manager |
| Traces | Cloud Trace + OTEL | ADOT -> CloudWatch / X-Ray |
| Logs | Cloud Logging | CloudWatch Logs |
| Runtime | Agent Engine / Cloud Run | EKS / ECS Fargate |

---

## Tool Error Handling Convention

All tools return a dict with a `"status"` key:

```python
# Success
{"status": "success", ...}

# Failure — never raises, always returns structured error
{"status": "error", "message": "..."}

# Blocked by Bedrock Guardrail
{"status": "blocked", "reason": "..."}
```

---

## Switching Bedrock Models

Update model vars in `.env`:

| Model | LiteLLM string |
|---|---|
| Claude Sonnet 4.5 | `bedrock/anthropic.claude-sonnet-4-5` |
| Claude Opus 4.5 | `bedrock/anthropic.claude-opus-4-5` |
| Claude Haiku 4.5 | `bedrock/anthropic.claude-haiku-4-5-20251001` |
| Amazon Nova Pro | `bedrock/amazon.nova-pro-v1:0` |
| Llama 3.1 70B | `bedrock/meta.llama3-1-70b-instruct-v1:0` |

---

## Phased Rollout

| Phase | What to build | Risk |
|---|---|---|
| 1 | RAGAgent only — read-only Bedrock KB answers | Low |
| 2 | Add ActionAgent — tickets and lookups | Medium |
| 3 | Add PolicyAgent + Guardrails — govern all actions | Low (adds safety) |
| 4 | Add domain specialists — HR, ops, finance | Medium |

---

## Production Deployment

Deploy to **ECS Fargate** or **EKS** with an IAM task/pod role.

```bash
# Build and push to ECR
docker build -t enterprise-agent-aws .
aws ecr create-repository --repository-name enterprise-agent-aws --region us-east-1
docker tag enterprise-agent-aws:latest <account>.dkr.ecr.us-east-1.amazonaws.com/enterprise-agent-aws:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/enterprise-agent-aws:latest
```

See `SETUP.md` for the complete deployment guide.
