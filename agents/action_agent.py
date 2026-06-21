"""
Action / Workflow Agent
Executes controlled actions against enterprise systems: tickets, lookups, API calls.
All write actions must pass through PolicyAgent first.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools import get_ticket_status, create_ticket
from config import ACTION_MODEL

action_agent = LlmAgent(
    name="ActionAgent",
    model=LiteLlm(model=ACTION_MODEL),
    description=(
        "Executes actions against enterprise systems: ticket lookup, "
        "ticket creation, system record retrieval, and workflow triggering."
    ),
    instruction="""
        You are the enterprise Action and Workflow Agent.

        Your responsibilities:
        1. Execute the requested action using the available tools.
        2. Always confirm the action you are about to take before executing it.
        3. Report the result clearly — include IDs, states, and next steps.
        4. If an action fails, explain why and suggest alternatives.
        5. Never take destructive or irreversible actions without explicit user confirmation.

        Available actions: ticket lookup, ticket creation.
        For actions not covered by your tools, tell the user and suggest who can help.
    """,
    tools=[get_ticket_status, create_ticket],
)
