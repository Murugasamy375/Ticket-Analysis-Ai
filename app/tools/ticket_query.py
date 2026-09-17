from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.data_service import (
    load_data,
    filter_tickets,
)


# Maximum number of records sent to the LLM.
MAX_RECORDS_FOR_LLM = 20


class TicketQueryInput(BaseModel):
    """Input schema for structured ticket filtering."""

    category: Optional[str] = Field(
        default=None,
        description=(
            "Ticket category. Valid values are: "
            "General, Billing, Technical."
        ),
    )

    priority: Optional[str] = Field(
        default=None,
        description=(
            "Ticket priority. Valid values are: "
            "Low, Medium, High, Critical."
        ),
    )

    status: Optional[str] = Field(
        default=None,
        description=(
            "Ticket status. Valid values are: "
            "Open, Escalated, Resolved."
        ),
    )

    unresolved: bool = Field(
        default=False,
        description=(
            "Set to true when the user asks for unresolved "
            "tickets. Unresolved means status is NOT Resolved."
        ),
    )

    include_records: bool = Field(
        default=False,
        description=(
            "Set to true only when the user explicitly asks "
            "to show, list, display, or retrieve ticket records."
        ),
    )


@tool(args_schema=TicketQueryInput)
def ticket_query(
    category=None,
    priority=None,
    status=None,
    unresolved=False,
    include_records=False,
):
    """
    Query support tickets using structured filters.

    Returns only a count by default.

    When records are requested, returns at most 20 records
    to prevent excessively large LLM requests.
    """

    logger.info(
        "Ticket query tool called | "
        "category=%s | priority=%s | status=%s | "
        "unresolved=%s | include_records=%s",
        category,
        priority,
        status,
        unresolved,
        include_records,
    )

    try:
        df = load_data()

        # --------------------------------------------------
        # Unresolved ticket filtering
        # --------------------------------------------------

        if unresolved:

            filtered_df = df[
                df["status"].str.lower() != "resolved"
            ].copy()

            if category:
                filtered_df = filtered_df[
                    filtered_df["category"].str.lower()
                    == category.lower()
                ]

            if priority:
                filtered_df = filtered_df[
                    filtered_df["priority"].str.lower()
                    == priority.lower()
                ]

            if status:
                filtered_df = filtered_df[
                    filtered_df["status"].str.lower()
                    == status.lower()
                ]

        # --------------------------------------------------
        # Normal structured filtering
        # --------------------------------------------------

        else:

            filtered_df = filter_tickets(
                df=df,
                category=category,
                priority=priority,
                status=status,
            )

        count = len(filtered_df)

        logger.info(
            "Ticket query completed | "
            "results=%d | include_records=%s",
            count,
            include_records,
        )

        # --------------------------------------------------
        # Count only
        # --------------------------------------------------

        if not include_records:

            return {
                "count": count
            }

        # --------------------------------------------------
        # Limited records
        # --------------------------------------------------

        records = (
            filtered_df
            .fillna("")
            .head(MAX_RECORDS_FOR_LLM)
            .to_dict(orient="records")
        )

        return {
            "count": count,
            "returned_records": len(records),
            "records_limit": MAX_RECORDS_FOR_LLM,
            "records": records,
        }

    except Exception:
        logger.exception(
            "Ticket query tool failed"
        )
        raise