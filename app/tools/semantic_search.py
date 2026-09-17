from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.rag_service import rag_service


class SemanticSearchInput(BaseModel):
    """Input schema for semantic ticket search."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description=(
            "Natural-language description of the issue to search for. "
            "Use this for meaning-based or free-text questions."
        ),
    )

    n_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of relevant tickets to retrieve.",
    )


@tool(args_schema=SemanticSearchInput)
def semantic_search(
    query: str,
    n_results: int = 10,
):
    """
    Search support tickets using semantic similarity.
    """

    logger.info(
        "Semantic search tool called | query=%s | n_results=%d",
        query,
        n_results,
    )

    try:
        results = rag_service.search(
            query=query,
            n_results=n_results,
        )

        logger.info(
            "Semantic search tool completed | results=%d",
            len(results),
        )

        return results

    except Exception:
        logger.exception(
            "Semantic search tool failed"
        )
        raise