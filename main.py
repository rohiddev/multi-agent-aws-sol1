"""
Enterprise Multi-Agent System — AWS Bedrock entry point.

Architecture:
  SupervisorAgent (Claude on Bedrock via LiteLLM)
    ├── RAGAgent        — Bedrock Knowledge Bases retrieval
    ├── ActionAgent     — enterprise system actions
    └── PolicyAgent     — Bedrock Guardrails + IAM policy checks

Model backend:  Amazon Bedrock (via LiteLLM)
RAG backend:    Amazon Bedrock Knowledge Bases (boto3)
Guardrails:     Amazon Bedrock Guardrails
Observability:  OpenTelemetry → ADOT → CloudWatch / X-Ray
Security:       IAM roles + Secrets Manager + PrivateLink
"""

import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import APP_NAME
from agents import supervisor_agent
from observability import setup_telemetry, trace_agent_call

USER_ID    = "user-001"
SESSION_ID = "session-001"


async def run(query: str) -> str:
    tracer = setup_telemetry()
    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        agent=supervisor_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    with trace_agent_call(tracer, "SupervisorAgent", USER_ID, SESSION_ID):
        message = types.Content(
            role="user",
            parts=[types.Part(text=query)],
        )
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message,
        ):
            if event.is_final_response():
                return event.content.parts[0].text

    return "No response."


if __name__ == "__main__":
    # Phase 1: knowledge question → RAGAgent → Bedrock Knowledge Base
    result = asyncio.run(run("What is the company policy on remote access to production systems?"))
    print("AGENT:", result)

    # Phase 2: action request → PolicyAgent → ActionAgent
    result = asyncio.run(run("Create a P2 ticket: VPN access is broken for the payments team."))
    print("AGENT:", result)
