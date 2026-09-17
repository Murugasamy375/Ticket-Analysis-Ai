import os

import chromadb
from sentence_transformers import SentenceTransformer

from app.core.logger import logger
from app.services.data_service import load_data


# --------------------------------------------------
# Configuration
# --------------------------------------------------

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "support_tickets"

# Hugging Face embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# --------------------------------------------------
# Knowledge Base
# --------------------------------------------------

class TicketKnowledgeBase:

    def __init__(self):
        logger.info("Initializing ticket knowledge base")

        # Load Hugging Face embedding model
        self.embedding_model = SentenceTransformer(
            EMBEDDING_MODEL
        )

        logger.info(
            "Embedding model loaded | model=%s",
            EMBEDDING_MODEL
        )

        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=CHROMA_PATH
        )

        # Create or load collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            }
        )

        logger.info(
            "ChromaDB collection ready | collection=%s",
            COLLECTION_NAME
        )


    # --------------------------------------------------
    # Convert CSV row → Document
    # --------------------------------------------------

    def create_document(self, row) -> str:

        return f"""
Ticket ID: {row['ticket_id']}
Created At: {row['created_at']}
Category: {row['category']}
Priority: {row['priority']}
Status: {row['status']}
Response Time: {row['response_time_hrs']} hours
Resolution Time: {row['resolution_time_hrs']} hours
Agent ID: {row['agent_id']}
Customer Rating: {row['customer_rating']}
Issue Summary: {row['issue_summary']}
""".strip()


    # --------------------------------------------------
    # Build Knowledge Base
    # --------------------------------------------------

    def build_knowledge_base(self):

        logger.info("Building ticket knowledge base")

        try:

            # Load complete CSV
            df = load_data()

            documents = []
            ids = []
            metadatas = []

            # Create one document per ticket
            for _, row in df.iterrows():

                document = self.create_document(row)

                documents.append(document)

                ids.append(
                    str(row["ticket_id"])
                )

                # Store useful structured metadata
                metadatas.append({
                    "ticket_id": str(row["ticket_id"]),
                    "category": str(row["category"]),
                    "priority": str(row["priority"]),
                    "status": str(row["status"]),
                    "agent_id": str(row["agent_id"])
                })


            logger.info(
                "Generating embeddings | documents=%d",
                len(documents)
            )

            # Generate Hugging Face embeddings
            embeddings = self.embedding_model.encode(
                documents,
                show_progress_bar=True
            ).tolist()


            # Store everything in ChromaDB
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )


            logger.info(
                "Knowledge base built successfully | documents=%d",
                len(documents)
            )

            return {
                "status": "success",
                "documents": len(documents),
                "collection": COLLECTION_NAME
            }

        except Exception:

            logger.exception(
                "Failed to build knowledge base"
            )

            raise


    # --------------------------------------------------
    # Semantic Search
    # --------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 10
    ):

        logger.info(
            "Semantic search started | query=%s",
            query
        )

        try:

            # Convert user query into embedding
            query_embedding = self.embedding_model.encode(
                [query]
            ).tolist()


            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )


            logger.info(
                "Semantic search completed | results=%d",
                len(results["ids"][0])
            )

            return results

        except Exception:

            logger.exception(
                "Semantic search failed"
            )

            raise


# --------------------------------------------------
# Global Knowledge Base Instance
# --------------------------------------------------

knowledge_base = TicketKnowledgeBase()