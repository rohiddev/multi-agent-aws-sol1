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
            ← S3 / SharePoint / Confluence / OneDrive / web

Security
    ├── IAM roles + least-privilege policies
    ├── Bedrock Guardrails (blocked topics, PII, grounding)
    ├── AWS Secrets Manager
    └── PrivateLink / VPC endpoints for Bedrock

Observability
    ├── OpenTelemetry → ADOT → CloudWatch / X-Ray
    └── CloudWatch Logs (structured)
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure AWS credentials
aws configure

# 3. Enable Bedrock model access
# AWS Console → Bedrock → Model access → enable Claude models

# 4. Configure environment
cp .env.example .env
# Edit .env with your AWS region, model IDs, Knowledge Base ID

# 5. Run
adk web multi_agent_aws_sol1/
```

See `SETUP.md` for the complete local and AWS deployment guide.

---

## Folder Structure

```
multi_agent_aws_sol1/
├── agent.py                     # ADK CLI entry point (root_agent)
├── main.py                      # Direct Python entry point
├── config.py                    # Config from environment variables
├── requirements.txt
├── .env.example
├── README.md
├── SETUP.md                     # Local + AWS deployment steps
├── agents/
│   ├── supervisor.py            # Supervisor — routes to specialist agents
│   ├── rag_agent.py             # RAG agent — Bedrock Knowledge Bases
│   ├── action_agent.py          # Action agent — tickets, APIs
│   └── policy_agent.py          # Policy agent — Guardrails + IAM
├── retrieval/
│   └── retrieval.py             # Bedrock Knowledge Bases (boto3)
├── tools/
│   └── enterprise_tools.py      # Tool definitions with Guardrail checks
├── observability/
│   └── telemetry.py             # OpenTelemetry → ADOT → CloudWatch
└── security/
    └── aws_security.py          # IAM, Secrets Manager, Guardrails
```

---

## GCP vs AWS — Side by Side

| Component | GCP version (sol1) | AWS version (sol1) |
|---|---|---|
| Agent framework | Google ADK | Google ADK |
| Model | Gemini (native) | Claude on Bedrock (LiteLLM) |
| RAG | Agent Search / RAG Engine / Vector Search | Bedrock Knowledge Bases |
| Guardrails / Safety | Policy Agent + IAM | Bedrock Guardrails + IAM |
| Secrets | Secret Manager | Secrets Manager |
| Traces | Cloud Trace + OTEL | ADOT → CloudWatch / X-Ray |
| Logs | Cloud Logging | CloudWatch Logs |
| Runtime | Agent Engine / Cloud Run | EKS / ECS Fargate |

---

## Phased Rollout

| Phase | What to build | Risk |
|---|---|---|
| 1 | RAGAgent only — read-only Bedrock KB answers | Low |
| 2 | Add ActionAgent — tickets and lookups | Medium |
| 3 | Add PolicyAgent + Guardrails — govern all actions | Low (adds safety) |
| 4 | Add domain specialists — HR, ops, finance | Medium |
