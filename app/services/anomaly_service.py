import pandas as pd

from app.core.logger import logger
from app.services.data_service import load_data


class AnomalyService:
    """Service for detecting anomalies in support tickets."""

    def __init__(self):
        logger.info("Initializing anomaly service")

    def detect_long_resolution_tickets(
        self,
        threshold_hours: float = 24.0
    ) -> list[dict]:
        """Find resolved tickets with unusually long resolution times."""

        logger.info(
            "Checking long resolution times | threshold=%.1f hours",
            threshold_hours
        )

        df = load_data()

        anomalies = df[
            (df["status"].str.lower() == "resolved")
            & (df["resolution_time_hrs"] > threshold_hours)
        ].copy()

        logger.info(
            "Long resolution check completed | anomalies=%d",
            len(anomalies)
        )

        return anomalies.fillna("").to_dict(orient="records")

    def detect_old_unresolved_high_priority(
        self,
        age_threshold_hours: float = 24.0
    ) -> list[dict]:
        """Find unresolved high-priority tickets older than the threshold."""

        logger.info(
            "Checking old unresolved high-priority tickets | threshold=%.1f hours",
            age_threshold_hours
        )

        df = load_data()

        # Use the latest ticket creation time as the dataset reference time.
        reference_time = df["created_at"].max()

        unresolved = df[
            df["status"].str.lower() != "resolved"
        ].copy()

        high_priority = unresolved[
            unresolved["priority"].str.lower().isin(["high", "critical"])
        ].copy()

        high_priority["age_hours"] = (
            (reference_time - high_priority["created_at"])
            .dt.total_seconds() / 3600
        )

        anomalies = high_priority[
            high_priority["age_hours"] > age_threshold_hours
        ].copy()

        logger.info(
            "Old unresolved high-priority check completed | anomalies=%d",
            len(anomalies)
        )

        return anomalies.fillna("").to_dict(orient="records")

    def detect_all(
        self,
        resolution_time_threshold: float = 24.0,
        unresolved_age_threshold: float = 24.0
    ) -> dict:
        """Run all anomaly checks and return a compact result."""

        logger.info("Running all anomaly checks")

        long_resolution = self.detect_long_resolution_tickets(
            resolution_time_threshold
        )

        old_unresolved = self.detect_old_unresolved_high_priority(
            unresolved_age_threshold
        )

        result = {
            "long_resolution_count": len(long_resolution),
            "old_unresolved_high_priority_count": len(old_unresolved),
            "total_anomalies": (
                len(long_resolution) + len(old_unresolved)
            ),

            # Only send a few examples to the LLM.
            "long_resolution_samples": long_resolution[:5],
            "old_unresolved_high_priority_samples": old_unresolved[:5],
        }

        logger.info(
            "All anomaly checks completed | total_anomalies=%d",
            result["total_anomalies"]
        )

        return result


anomaly_service = AnomalyService()