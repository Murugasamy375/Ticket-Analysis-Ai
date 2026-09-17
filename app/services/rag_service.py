from app.core.logger import logger
from app.rag.rag import knowledge_base


class RAGService:
    """Service layer for semantic retrieval from the ticket knowledge base."""

    def __init__(self):
        logger.info("Initializing RAG service")

    def search(
        self,
        query: str,
        n_results: int = 10,
    ) -> list[dict]:
        """
        Perform semantic search over support tickets.
        """

        logger.info(
            "RAG search requested | query=%s | n_results=%d",
            query,
            n_results,
        )

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if n_results < 1:
            raise ValueError("n_results must be greater than 0.")

        try:
            results = knowledge_base.search(
                query=query,
                n_results=n_results,
            )

            logger.info(
                "RAG search completed | results=%d",
                len(results),
            )

            return results

        except Exception:
            logger.exception("RAG search failed")
            raise


rag_service = RAGService()