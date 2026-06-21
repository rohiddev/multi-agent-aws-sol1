"""
RAG / Search Agent
Retrieves grounded answers from Amazon Bedrock Knowledge Bases.
Supports classic RAG and agentic RAG (multi-hop, multi-source retrieval).
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext
from retrieval import retrieve
from config import RAG_MODEL


def search_enterprise_knowledge(query: str, tool_context: ToolContext) -> dict:
    """Search Bedrock Knowledge Base and return grounded results.

    Args:
        query: The question or search phrase to retrieve information for.

    Returns:
        dict: status, results list, and source count.
    """
    results = retrieve(query, top_k=5)
    tool_context.state["last_retrieval_query"]   = query
    tool_context.state["last_retrieval_results"] = results
    return {
        "status":       "success",
        "results":      results,
        "result_count": len(results),
    }


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
        4. For complex questions, call the tool multiple times with different queries (agentic RAG).
        5. If no relevant results are found, say so clearly.

        Format: answer first, then sources.
    """,
    tools=[search_enterprise_knowledge],
)
