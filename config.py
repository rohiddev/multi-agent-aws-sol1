import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

SUPERVISOR_MODEL = os.getenv("SUPERVISOR_MODEL", "bedrock/anthropic.claude-sonnet-4-5")
RAG_MODEL        = os.getenv("RAG_MODEL",        "bedrock/anthropic.claude-sonnet-4-5")
ACTION_MODEL     = os.getenv("ACTION_MODEL",     "bedrock/anthropic.claude-sonnet-4-5")
POLICY_MODEL     = os.getenv("POLICY_MODEL",     "bedrock/anthropic.claude-opus-4-5")

KNOWLEDGE_BASE_ID  = os.getenv("KNOWLEDGE_BASE_ID", "")
GUARDRAIL_ID       = os.getenv("GUARDRAIL_ID", "")
GUARDRAIL_VERSION  = os.getenv("GUARDRAIL_VERSION", "DRAFT")

APP_NAME  = os.getenv("APP_NAME", "enterprise-multi-agent-aws")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
