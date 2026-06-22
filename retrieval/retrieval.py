"""
Retrieval layer — Amazon Bedrock Knowledge Bases.

Bedrock Knowledge Bases handle ingestion, chunking, embedding, indexing,
and retrieval automatically. Supported data sources:
  - Amazon S3 (PDFs, Word docs, HTML, CSV, text)
  - SharePoint / Confluence / OneDrive / Salesforce / web crawl

Set KNOWLEDGE_BASE_ID in .env with your Bedrock KB ID.
If KNOWLEDGE_BASE_ID is not set, stub results are returned (dev mode).
"""

import logging
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, KNOWLEDGE_BASE_ID

logger = logging.getLogger(__name__)

_client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant documents from Bedrock Knowledge Base.

    Args:
        query: Natural language query string.
        top_k: Number of results to return.

    Returns:
        list of dicts with keys: content, source, score.
    """
    if not KNOWLEDGE_BASE_ID:
        logger.warning("KNOWLEDGE_BASE_ID not set — returning stub results (dev mode)")
        return [{"content": f"[stub] Results for: {query}", "source": "stub", "score": 0.0}]

    try:
        response = _client.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": top_k}
            },
        )
        results = []
        for r in response.get("retrievalResults", []):
            results.append({
                "content": r["content"]["text"],
                "source":  r.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
                "score":   r.get("score", 0.0),
            })
        logger.info("bedrock_kb retrieved %d results for query=%s", len(results), query)
        return results

    except ClientError as e:
        logger.error("bedrock_kb retrieve failed: %s", e)
        return []
