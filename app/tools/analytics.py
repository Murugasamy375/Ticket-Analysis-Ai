from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.analytics_service import analytics_service


class AnalyticsInput(BaseModel):
    """Input schema for analytics operations."""

    operation: str = Field(
        description=(
            "Analytics operation to perform. "
            "Allowed operations: count, resolved_count, "
            "unresolved_count, average_rating, "
            "average_response_time, average_resolution_time, "
            "count_by_category, count_by_priority, "
            "count_by_status, count_by_agent, "
            "average_rating_by_agent."
        )
    )

    category: Optional[str] = Field(
        default=None,
        description="Optional ticket category filter."
    )

    priority: Optional[str] = Field(
        default=None,
        description="Optional ticket priority filter."
    )

    status: Optional[str] = Field(
        default=None,
        description="Optional ticket status filter."
    )


@tool(args_schema=AnalyticsInput)
def analytics(
    operation: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    """
    Perform structured analytics on support tickets.
    """

    logger.info(
        "Analytics tool called | operation=%s",
        operation,
    )

    operation = operation.lower().strip()

    if operation == "count":

        result = analytics_service.count_tickets(
            category,
            priority,
            status,
        )

    elif operation == "resolved_count":

        result = analytics_service.count_resolved(
            category,
            priority,
            status,
        )

    elif operation == "unresolved_count":

        result = analytics_service.count_unresolved(
            category,
            priority,
            status,
        )

    elif operation == "average_rating":

        result = analytics_service.average_rating(
            category,
            priority,
            status,
        )

    elif operation == "average_response_time":

        result = analytics_service.average_response_time(
            category,
            priority,
            status,
        )

    elif operation == "average_resolution_time":

        result = analytics_service.average_resolution_time(
            category,
            priority,
            status,
        )

    elif operation == "count_by_category":

        result = analytics_service.count_by_category()

    elif operation == "count_by_priority":

        result = analytics_service.count_by_priority()

    elif operation == "count_by_status":

        result = analytics_service.count_by_status()

    elif operation == "count_by_agent":

        result = analytics_service.count_by_agent()

    elif operation == "average_rating_by_agent":

        result = analytics_service.average_rating_by_agent()

    else:
        raise ValueError(
            f"Unsupported analytics operation: {operation}"
        )

    return {
        "status": "success",
        "operation": operation,
        "result": result,
    }