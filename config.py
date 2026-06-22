import os
from dotenv import load_dotenv

load_dotenv()

VALID_BEDROCK_REGIONS = {
    "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
    "ap-southeast-1", "ap-northeast-1", "ap-south-1",
}


def _require(key: str) -> str:
    """Return a required environment variable or raise with a clear message."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in your values."
        )
    return val


def _optional(key: str, default: str) -> str:
    """Return an optional environment variable, falling back to default."""
    return os.getenv(key, default)


# --- AWS ---
AWS_REGION = _optional("AWS_REGION", "us-east-1")

if AWS_REGION not in VALID_BEDROCK_REGIONS:
    raise EnvironmentError(
        f"AWS_REGION='{AWS_REGION}' does not support Bedrock. "
        f"Valid values: {sorted(VALID_BEDROCK_REGIONS)}"
    )

# --- Model selection (LiteLLM bedrock/ prefix) ---
SUPERVISOR_MODEL = _optional("SUPERVISOR_MODEL", "bedrock/anthropic.claude-sonnet-4-5")
RAG_MODEL        = _optional("RAG_MODEL",        "bedrock/anthropic.claude-sonnet-4-5")
ACTION_MODEL     = _optional("ACTION_MODEL",     "bedrock/anthropic.claude-sonnet-4-5")
POLICY_MODEL     = _optional("POLICY_MODEL",     "bedrock/anthropic.claude-opus-4-5")

# --- Bedrock Knowledge Base ---
KNOWLEDGE_BASE_ID = _optional("KNOWLEDGE_BASE_ID", "")

# --- Bedrock Guardrails (optional — leave blank to skip) ---
GUARDRAIL_ID      = _optional("GUARDRAIL_ID",      "")
GUARDRAIL_VERSION = _optional("GUARDRAIL_VERSION", "DRAFT")

# --- AWS Secrets Manager namespace (optional) ---
SECRETS_NAMESPACE = _optional("SECRETS_NAMESPACE", "enterprise-agent")

# --- Application ---
APP_NAME  = _optional("APP_NAME",  "enterprise-multi-agent-aws")
LOG_LEVEL = _optional("LOG_LEVEL", "INFO")
