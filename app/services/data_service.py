import os
import pandas as pd

from app.core.logger import logger


DATA_PATH = "data/support_tickets.csv"

EXPECTED_COLUMNS = [
    "ticket_id",
    "created_at",
    "category",
    "priority",
    "status",
    "response_time_hrs",
    "resolution_time_hrs",
    "agent_id",
    "customer_rating",
    "issue_summary",
]


def load_data() -> pd.DataFrame:
    """Load and validate the support tickets CSV."""

    logger.info("Loading dataset | path=%s", DATA_PATH)

    try:
        if not os.path.exists(DATA_PATH):
            logger.error("Dataset not found | path=%s", DATA_PATH)
            raise FileNotFoundError(
                f"Dataset not found: {DATA_PATH}"
            )

        df = pd.read_csv(DATA_PATH)

        logger.info(
            "Dataset loaded | rows=%d | columns=%d",
            len(df),
            len(df.columns)
        )

        # Validate required columns
        missing_columns = [
            column
            for column in EXPECTED_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:
            logger.error(
                "Missing required columns | columns=%s",
                missing_columns
            )
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        # Keep only the expected columns
        df = df[EXPECTED_COLUMNS]

        # Convert date column
        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

        invalid_dates = df["created_at"].isna().sum()

        if invalid_dates > 0:
            logger.warning(
                "Invalid created_at values | count=%d",
                invalid_dates
            )

        logger.info("Dataset validation completed successfully")

        return df

    except Exception:
        logger.exception("Failed to load dataset")
        raise
def get_dataset_info(df: pd.DataFrame) -> dict:
    """Return dataset metadata and summary statistics."""

    logger.info("Generating dataset information")

    try:
        column_details = []

        for column in df.columns:
            column_details.append({
                "name": column,
                "dtype": str(df[column].dtype),
                "non_null": int(df[column].notna().sum()),
                "null_count": int(df[column].isna().sum()),
                "unique_count": int(df[column].nunique())
            })

        info = {
            "filename": os.path.basename(DATA_PATH),
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": column_details,
            "statistics": {
                "resolved_tickets": int(
                    (df["status"] == "Resolved").sum()
                ),
                "unresolved_tickets": int(
                    (df["status"] != "Resolved").sum()
                ),
                "critical_tickets": int(
                    (df["priority"] == "Critical").sum()
                ),
                "high_priority_tickets": int(
                    (df["priority"] == "High").sum()
                ),
                "categories": int(
                    df["category"].nunique()
                ),
                "agents": int(
                    df["agent_id"].nunique()
                )
            }
        }

        logger.info(
            "Dataset information generated | rows=%d | columns=%d",
            len(df),
            len(df.columns)
        )

        return info

    except Exception:
        logger.exception("Failed to generate dataset information")
        raise
def filter_tickets(
    df: pd.DataFrame,
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    ticket_id: str | None = None,
) -> pd.DataFrame:
    logger.info(
        "Applying ticket filters | category=%s | priority=%s | status=%s | ticket_id=%s",
        category,
        priority,
        status,
        ticket_id,
    )

    try:
        filtered_df = df.copy()

        if category:
            filtered_df = filtered_df[
                filtered_df["category"].str.lower() == category.lower()
            ]

        if priority:
            filtered_df = filtered_df[
                filtered_df["priority"].str.lower() == priority.lower()
            ]

        if status:
            filtered_df = filtered_df[
                filtered_df["status"].str.lower() == status.lower()
            ]

        if ticket_id:
            filtered_df = filtered_df[
                filtered_df["ticket_id"].str.lower() == ticket_id.lower()
            ]

        logger.info(
            "Ticket filtering completed | results=%d",
            len(filtered_df),
        )

        return filtered_df

    except Exception:
        logger.exception("Ticket filtering failed")
        raise