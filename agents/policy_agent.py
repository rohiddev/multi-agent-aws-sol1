"""
Policy / Risk Agent
Checks permissions, flags sensitive data, and applies Bedrock Guardrails
before any action is executed.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools import check_policy
from config import POLICY_MODEL

policy_agent = LlmAgent(
    name="PolicyAgent",
    model=LiteLlm(model=POLICY_MODEL),
    description=(
        "Evaluates requests against enterprise policy and Bedrock Guardrails. "
        "Determines whether an action is permitted, flags sensitive data, "
        "and decides if human approval is required."
    ),
    instruction="""
        You are the enterprise Policy and Risk Agent, backed by Amazon Bedrock Guardrails.

        Your responsibilities:
        1. Use check_policy to verify the requested action is permitted for the user's role.
        2. Flag any sensitive data categories (PII, PHI, financial, confidential).
        3. If the action is NOT permitted, respond with DENIED and the reason. Do not proceed.
        4. If the action IS permitted but involves sensitive data, respond with REQUIRES_APPROVAL.
        5. If the action is fully permitted and low-risk, respond with PERMITTED.

        Always be explicit: PERMITTED | DENIED | REQUIRES_APPROVAL.
    """,
    tools=[check_policy],
)
