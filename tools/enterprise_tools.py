"""
Enterprise tool definitions.
Each function is a plain Python function — ADK converts them into callable tools automatically.
Add new tools here and pass them to the relevant agent's tools= list.

Error handling convention: all tools return a dict with "status": "success" | "error" | "blocked".
Agents should check status and handle errors gracefully rather than crashing.

Guardrail convention: sensitive inputs are checked via apply_guardrail before processing.
If a guardrail fires, the tool returns {"status": "blocked", "reason": "..."} and stops.
"""

import logging
from google.adk.tools.tool_context import ToolContext
from retrieval import retrieve
from security import apply_guardrail

logger = logging.getLogger(__name__)


def search_enterprise_knowledge(query: str, tool_context: ToolContext) -> dict:
    """Search Amazon Bedrock Knowledge Base and return grounded results.

    Args:
        query: Natural language question or search phrase to retrieve information for.

    Returns:
        dict: status, results list, and result_count.
    """
    try:
        logger.info("search_enterprise_knowledge query=%s", query)
        guard = apply_guardrail(query, source="INPUT")
        if guard["action"] == "GUARDRAIL_INTERVENED":
            return {"status": "blocked", "reason": "query blocked by enterprise guardrail", "results": [], "result_count": 0}

        results = retrieve(query, top_k=5)
        tool_context.state["last_retrieval_query"]   = query
        tool_context.state["last_retrieval_results"] = results
        return {
            "status":       "success",
            "results":      results,
            "result_count": len(results),
        }
    except Exception as e:
        logger.exception("search_enterprise_knowledge failed query=%s", query)
        return {"status": "error", "message": str(e), "results": [], "result_count": 0}


def get_ticket_status(ticket_id: str) -> dict:
    """Retrieve the current status of a service ticket or work item.

    Args:
        ticket_id: The ticket identifier (e.g. INC0012345).

    Returns:
        dict: status and ticket details.
    """
    try:
        logger.info("get_ticket_status ticket_id=%s", ticket_id)
        # Replace with real ticketing system API call (ServiceNow, Jira, etc.)
        return {"status": "success", "ticket": {"id": ticket_id, "state": "open", "priority": "P2"}}
    except Exception as e:
        logger.exception("get_ticket_status failed ticket_id=%s", ticket_id)
        return {"status": "error", "message": str(e)}


def create_ticket(summary: str, description: str, priority: str = "P3") -> dict:
    """Create a new service ticket in the ticketing system.

    Args:
        summary: One-line summary of the issue.
        description: Full description of the request.
        priority: P1 | P2 | P3 | P4 (default P3).

    Returns:
        dict: status and new ticket ID.
    """
    try:
        logger.info("create_ticket summary=%s priority=%s", summary, priority)
        # Apply guardrail to the summary before creating the ticket
        guard = apply_guardrail(summary, source="INPUT")
        if guard["action"] == "GUARDRAIL_INTERVENED":
            return {"status": "blocked", "reason": "ticket creation blocked by enterprise guardrail"}

        # Replace with real ticketing system API call (ServiceNow, Jira, etc.)
        return {"status": "success", "ticket_id": "INC0099999"}
    except Exception as e:
        logger.exception("create_ticket failed summary=%s", summary)
        return {"status": "error", "message": str(e)}


def check_policy(action: str, user_role: str, resource: str) -> dict:
    """Check whether the requested action is permitted under enterprise policy.

    Args:
        action: The action being requested (e.g. 'delete', 'read', 'approve').
        user_role: The role of the requesting user.
        resource: The resource being accessed.

    Returns:
        dict: allowed (bool) and reason.
    """
    try:
        logger.info("check_policy action=%s role=%s resource=%s", action, user_role, resource)
        # Replace with actual IAM policy check, OPA, or AWS Verified Access call
        allowed = action in ("read", "search", "create_ticket")
        return {
            "allowed": allowed,
            "reason": "permitted by enterprise policy" if allowed else "action requires elevated access",
        }
    except Exception as e:
        logger.exception("check_policy failed action=%s", action)
        return {"allowed": False, "reason": f"policy check error: {e}"}
