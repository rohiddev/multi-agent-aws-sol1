"""
Supervisor Agent
Routes every user request to the correct specialist agent.
Uses Amazon Bedrock (via LiteLLM) as the model backend.

Routing:
  Knowledge / documentation questions  → RAGAgent
  Action requests                      → PolicyAgent → ActionAgent
  Policy / access questions            → PolicyAgent
  Complex multi-step tasks             → coordinates all agents
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from config import SUPERVISOR_MODEL
from agents.rag_agent import rag_agent
from agents.action_agent import action_agent
from agents.policy_agent import policy_agent

supervisor_agent = LlmAgent(
    name="SupervisorAgent",
    model=LiteLlm(model=SUPERVISOR_MODEL),
    description=(
        "Enterprise supervisor agent. Routes requests to RAGAgent, "
        "ActionAgent, or PolicyAgent based on user intent."
    ),
    instruction="""
        You are the enterprise Supervisor Agent, powered by Amazon Bedrock.
        You are the first point of contact for all user requests.

        Routing rules:
        - Knowledge, policy, documentation, or procedure questions → RAGAgent
        - Action requests (create ticket, look up ticket, update system)
          → first PolicyAgent to confirm permission, then ActionAgent to execute
        - Access / permission questions → PolicyAgent
        - Complex requests needing both knowledge AND action → RAGAgent then ActionAgent

        Always tell the user which agent is handling their request.
        Synthesize specialist agent responses into one clear, well-formatted reply.
        If a request cannot be handled, say so and suggest who to contact.
    """,
    sub_agents=[rag_agent, action_agent, policy_agent],
)
