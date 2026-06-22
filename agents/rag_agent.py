"""
RAG / Search Agent
Retrieves grounded answers from Amazon Bedrock Knowledge Bases.
Supports classic RAG and agentic RAG (multi-hop, multi-source retrieval).
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools import search_enterprise_knowledge
from config import RAG_MODEL

rag_agent = LlmAgent(
    name="RAGAgent",
    model=LiteLlm(model=RAG_MODEL),
    description=(
        "Retrieves accurate, grounded answers from enterprise knowledge sources "
        "via Amazon Bedrock Knowledge Bases. Sources include S3, SharePoint, "
        "Confluence, internal wikis, runbooks, and SOPs."
    ),
    instruction="""
        You are the enterprise Knowledge Retrieval Agent, powered by Amazon Bedrock Knowledge Bases.

        Your responsibilities:
        1. Use search_enterprise_knowledge to retrieve relevant information.
        2. Ground your answer strictly in the retrieved content — do not fabricate information.
        3. Always cite the source document for every claim.
        4. If the tool returns status "error" or "blocked", report it clearly — do not proceed.
        5. If no relevant results are found, say so clearly — do not fabricate information.
        6. For complex questions, call the tool multiple times with different queries (agentic RAG).

        Format: answer first, then sources.
    """,
    tools=[search_enterprise_knowledge],
)
