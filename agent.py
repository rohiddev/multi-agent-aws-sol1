# ADK CLI entry point — exposes root_agent for `adk run` and `adk web`
from agents.supervisor import supervisor_agent

root_agent = supervisor_agent
