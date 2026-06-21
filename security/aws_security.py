"""
AWS security patterns for enterprise agent deployment.

Production checklist:
  1. Run on IAM role (EKS/ECS) — never use long-lived access keys in production.
  2. Use least-privilege IAM policies scoped to bedrock:InvokeModel, bedrock:Retrieve.
  3. Enable PrivateLink / VPC endpoints for Bedrock runtime and agent runtime.
  4. Use KMS customer-managed keys for S3, Knowledge Base, and secrets encryption.
  5. Store all secrets in AWS Secrets Manager — never in environment variables in prod.
  6. Enable CloudTrail for all Bedrock API calls.
  7. Apply Bedrock Guardrails to every model call (see apply_guardrail below).

References:
  - docs.aws.amazon.com/bedrock/latest/userguide/security.html
  - docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
  - docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html
"""

import logging
import boto3
from config import AWS_REGION, GUARDRAIL_ID, GUARDRAIL_VERSION

logger = logging.getLogger(__name__)


def get_secret(secret_name: str) -> str:
    """Retrieve a secret value from AWS Secrets Manager.

    Args:
        secret_name: The name or ARN of the secret.

    Returns:
        The secret string value.
    """
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]


def apply_guardrail(text: str, source: str = "INPUT") -> dict:
    """Apply Bedrock Guardrails to a prompt or response.

    Args:
        text: The text to evaluate.
        source: INPUT (prompt) or OUTPUT (response).

    Returns:
        dict: action (NONE | GUARDRAIL_INTERVENED) and reason if blocked.
    """
    if not GUARDRAIL_ID:
        return {"action": "NONE"}

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    try:
        response = client.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[{"text": {"text": text}}],
        )
        action = response.get("action", "NONE")
        logger.info("guardrail action=%s source=%s", action, source)
        return {"action": action, "outputs": response.get("outputs", [])}
    except Exception as exc:
        logger.error("guardrail apply failed: %s", exc)
        return {"action": "NONE"}
