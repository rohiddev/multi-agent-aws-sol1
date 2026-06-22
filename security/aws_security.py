"""
AWS security patterns for enterprise agent deployment.

Production checklist:
  1. Attach an IAM role to your ECS task / EKS pod — never use long-lived keys.
  2. Use least-privilege: bedrock:InvokeModel, bedrock:Retrieve, bedrock:ApplyGuardrail only.
  3. Store secrets in AWS Secrets Manager — never in .env or environment variables.
  4. Enable VPC endpoints (PrivateLink) for Bedrock so traffic never leaves AWS.
  5. Enable AWS CloudTrail for audit logging of all Bedrock API calls.

Minimum IAM policy (attach to your service role):
  {
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
      }
    ]
  }

References:
  - docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html
  - docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
  - docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
"""

import logging
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from config import AWS_REGION, GUARDRAIL_ID, GUARDRAIL_VERSION, SECRETS_NAMESPACE

logger = logging.getLogger(__name__)


def get_identity() -> dict:
    """Validate AWS credentials and return the current caller identity.

    Used at startup to fail fast if credentials are missing or misconfigured.

    Returns:
        dict with UserId, Account, and Arn of the current IAM principal.

    Raises:
        EnvironmentError: If no valid credentials are found.
    """
    try:
        sts = boto3.client("sts", region_name=AWS_REGION)
        identity = sts.get_caller_identity()
        logger.info(
            "AWS identity validated account=%s arn=%s",
            identity["Account"],
            identity["Arn"],
        )
        return {
            "user_id": identity["UserId"],
            "account": identity["Account"],
            "arn":     identity["Arn"],
        }
    except NoCredentialsError:
        raise EnvironmentError(
            "No AWS credentials found. Run 'aws configure' for local development, "
            "or attach an IAM role to your ECS task / EKS pod in production."
        )
    except ClientError as e:
        raise EnvironmentError(f"AWS credential validation failed: {e}")


def get_secret(secret_name: str) -> str:
    """Retrieve a secret string from AWS Secrets Manager.

    Args:
        secret_name: The short name of the secret (namespace prefix is added automatically).
                     e.g. "db-password" -> "enterprise-agent/db-password"

    Returns:
        The secret string value.

    Raises:
        RuntimeError: If the secret cannot be retrieved.
    """
    full_name = f"{SECRETS_NAMESPACE}/{secret_name}"
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=full_name)
        logger.info("Retrieved secret name=%s", full_name)
        return response["SecretString"]
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret '{full_name}': {e}")


def apply_guardrail(text: str, source: str = "INPUT") -> dict:
    """Apply Bedrock Guardrails to text before processing.

    Guardrails can block: denied topics, harmful content, PII, prompt injection.
    If GUARDRAIL_ID is not configured, this is a no-op (returns NONE action).

    Args:
        text:   The text to evaluate (user input or model output).
        source: "INPUT" (user message) or "OUTPUT" (model response).

    Returns:
        dict with "action": "NONE" | "GUARDRAIL_INTERVENED" and optional "reason".
    """
    if not GUARDRAIL_ID:
        return {"action": "NONE"}

    try:
        client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        response = client.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[{"text": {"text": text}}],
        )
        action = response.get("action", "NONE")
        if action == "GUARDRAIL_INTERVENED":
            logger.warning("Guardrail intervened source=%s text_preview=%.80s", source, text)
            return {"action": action, "reason": str(response.get("outputs", ""))}
        return {"action": action}
    except ClientError as e:
        logger.error("apply_guardrail failed: %s", e)
        return {"action": "NONE", "error": str(e)}
