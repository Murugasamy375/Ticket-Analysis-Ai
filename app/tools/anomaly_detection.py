from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.anomaly_service import anomaly_service


class AnomalyDetectionInput(BaseModel):
    """Input schema for anomaly detection."""

    resolution_time_threshold: float = Field(
        default=24.0,
        gt=0,
        description=(
            "Resolution time threshold in hours "
            "for detecting unusually long resolutions."
        )
    )

    unresolved_age_threshold: float = Field(
        default=24.0,
        gt=0,
        description=(
            "Age threshold in hours for detecting "
            "old unresolved High or Critical tickets."
        )
    )


@tool(args_schema=AnomalyDetectionInput)
def anomaly_detection(
    resolution_time_threshold: float = 24.0,
    unresolved_age_threshold: float = 24.0,
) -> dict:
    """
    Detect anomalies in support tickets.
    """

    logger.info(
        "Anomaly detection tool called"
    )

    try:

        result = anomaly_service.detect_all(
            resolution_time_threshold=(
                resolution_time_threshold
            ),
            unresolved_age_threshold=(
                unresolved_age_threshold
            ),
        )

        return {
            "status": "success",
            "anomalies": result,
        }

    except Exception:
        logger.exception(
            "Anomaly detection tool failed"
        )
        raise