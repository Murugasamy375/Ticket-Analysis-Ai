import os
import subprocess
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.data_service import (
    load_data,
    get_dataset_info,
    filter_tickets,
)
from app.services.anomaly_service import anomaly_service
from app.llm.llm import llm, run_query


load_dotenv()


APP_NAME = os.getenv("APP_NAME", "Ticket AI Analytics")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


app = FastAPI(
    title=APP_NAME,
    description=(
        "AI-powered support ticket analytics, "
        "semantic search, and anomaly detection API."
    ),
    version="1.0.0",
)


streamlit_process = None


# ============================================================
# Request / Response Models
# ============================================================

class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language question about the support tickets.",
    )


class QueryResponse(BaseModel):
    query: str
    answer: str


class HealthResponse(BaseModel):
    status: str
    application: str
    environment: str
    dataset_loaded: bool
    rows: int
    llm_available: bool


class AnomalyResponse(BaseModel):
    long_resolution_count: int
    old_unresolved_high_priority_count: int
    total_anomalies: int
    long_resolution_samples: list[dict]
    old_unresolved_high_priority_samples: list[dict]


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def startup_event():
    global streamlit_process

    logger.info(
        "Starting application | environment=%s",
        ENVIRONMENT,
    )

    try:
        # Load and validate dataset
        df = load_data()

        logger.info(
            "Dataset loaded successfully | rows=%d",
            len(df),
        )

        # Start Streamlit UI
        streamlit_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "ui/app.py",
                "--server.port",
                "8501",
                "--server.address",
                "127.0.0.1",
                "--server.headless",
                "true",
            ]
        )

        logger.info(
            "Streamlit UI started | port=8501"
        )

        logger.info(
            "Application startup completed"
        )

    except Exception:
        logger.exception(
            "Application startup failed"
        )
        raise


# ============================================================
# Shutdown
# ============================================================

@app.on_event("shutdown")
def shutdown_event():
    global streamlit_process

    if streamlit_process is not None:

        logger.info(
            "Stopping Streamlit UI"
        )

        try:
            streamlit_process.terminate()

            streamlit_process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:

            logger.warning(
                "Streamlit did not stop gracefully; "
                "forcing termination"
            )

            streamlit_process.kill()

        except Exception:

            logger.exception(
                "Error while stopping Streamlit"
            )

        finally:

            streamlit_process = None

            logger.info(
                "Streamlit UI stopped"
            )


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():

    return {
        "application": APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "api": "http://127.0.0.1:8000",
        "docs": "http://127.0.0.1:8000/docs",
        "ui": "http://127.0.0.1:8501",
    }


# ============================================================
# Health Check
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check():

    logger.info(
        "Health check requested"
    )

    dataset_loaded = False
    rows = 0
    llm_available = False

    # Check dataset
    try:

        df = load_data()

        dataset_loaded = True
        rows = len(df)

    except Exception:

        logger.exception(
            "Dataset health check failed"
        )

    # Check LLM
    try:

        llm_available = llm is not None

    except Exception:

        logger.exception(
            "LLM health check failed"
        )

    overall_status = (
        "healthy"
        if dataset_loaded and llm_available
        else "unhealthy"
    )

    logger.info(
        "Health check completed | "
        "dataset=%s | rows=%d | llm=%s | status=%s",
        dataset_loaded,
        rows,
        llm_available,
        overall_status,
    )

    return {
        "status": overall_status,
        "application": APP_NAME,
        "environment": ENVIRONMENT,
        "dataset_loaded": dataset_loaded,
        "rows": rows,
        "llm_available": llm_available,
    }


# ============================================================
# Dataset Information
# ============================================================

@app.get("/dataset")
def dataset_information():

    logger.info(
        "Dataset information requested"
    )

    try:

        df = load_data()

        return get_dataset_info(df)

    except Exception:

        logger.exception(
            "Dataset information request failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to load dataset information.",
        )


# ============================================================
# Ticket Filtering
# ============================================================

@app.get("/filter")
def filter_ticket_data(

    category: str | None = Query(
        default=None,
        description="Filter by ticket category.",
    ),

    priority: str | None = Query(
        default=None,
        description="Filter by ticket priority.",
    ),

    status: str | None = Query(
        default=None,
        description="Filter by ticket status.",
    ),

    ticket_id: str | None = Query(
        default=None,
        description="Filter by ticket ID.",
    ),
):

    logger.info(
        "Filter endpoint called | "
        "category=%s | priority=%s | status=%s | ticket_id=%s",
        category,
        priority,
        status,
        ticket_id,
    )

    try:

        df = load_data()

        filtered_df = filter_tickets(
            df=df,
            category=category,
            priority=priority,
            status=status,
            ticket_id=ticket_id,
        )

        records = (
            filtered_df
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        logger.info(
            "Filter completed | results=%d",
            len(records),
        )

        return {
            "count": len(records),
            "records": records,
        }

    except Exception:

        logger.exception(
            "Filter request failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to filter tickets.",
        )


# ============================================================
# AI Natural Language Query
# ============================================================

@app.post(
    "/query",
    response_model=QueryResponse,
)
def ai_query(
    request: QueryRequest,
):

    logger.info(
        "AI query received | query=%s",
        request.query,
    )

    try:

        answer = run_query(
            request.query
        )

        logger.info(
            "AI query completed successfully"
        )

        return {
            "query": request.query,
            "answer": answer,
        }

    except Exception:

        logger.exception(
            "AI query failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process the AI query.",
        )


# ============================================================
# Anomaly Detection
# ============================================================

@app.get(
    "/anomalies",
    response_model=AnomalyResponse,
)
def detect_anomalies(
    resolution_time_threshold: float = Query(
        default=24.0,
        gt=0,
        description=(
            "Resolution time threshold in hours. "
            "Tickets above this value are flagged."
        ),
    ),
    unresolved_age_threshold: float = Query(
        default=24.0,
        gt=0,
        description=(
            "Age threshold in hours for unresolved "
            "high-priority tickets."
        ),
    ),
):
    logger.info(
        "Anomaly detection requested | "
        "resolution_threshold=%s | "
        "unresolved_age_threshold=%s",
        resolution_time_threshold,
        unresolved_age_threshold,
    )

    try:
        result = anomaly_service.detect_all(
            resolution_time_threshold=resolution_time_threshold,
            unresolved_age_threshold=unresolved_age_threshold,
        )

        logger.info(
            "Anomaly detection completed | "
            "total_anomalies=%d",
            result["total_anomalies"],
        )

        return result

    except Exception:
        logger.exception(
            "Anomaly detection failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to detect anomalies.",
        )