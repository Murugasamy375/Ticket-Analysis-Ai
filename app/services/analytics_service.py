from app.core.logger import logger
from app.services.data_service import load_data


class AnalyticsService:

    def __init__(self):
        logger.info("Initializing analytics service")

    def get_data(
        self,
        category: str | None = None,
        priority: str | None = None,
        status: str | None = None,
    ):
        """Load the dataset and apply optional filters."""

        logger.info(
            "Preparing analytics data | category=%s | priority=%s | status=%s",
            category,
            priority,
            status,
        )

        df = load_data()

        if category:
            df = df[
                df["category"].str.lower() == category.lower()
            ]

        if priority:
            df = df[
                df["priority"].str.lower() == priority.lower()
            ]

        if status:
            df = df[
                df["status"].str.lower() == status.lower()
            ]

        return df

    def count_tickets(
        self,
        category=None,
        priority=None,
        status=None,
    ) -> int:

        df = self.get_data(category, priority, status)

        result = len(df)

        logger.info("Ticket count calculated | count=%d", result)

        return int(result)

    def count_resolved(
        self,
        category=None,
        priority=None,
        status=None,
    ) -> int:

        df = self.get_data(category, priority, status)

        result = (
            df["status"].str.lower() == "resolved"
        ).sum()

        logger.info(
            "Resolved ticket count calculated | count=%d",
            result,
        )

        return int(result)

    def count_unresolved(
        self,
        category=None,
        priority=None,
        status=None,
    ) -> int:

        df = self.get_data(category, priority, status)

        result = (
            df["status"].str.lower() != "resolved"
        ).sum()

        logger.info(
            "Unresolved ticket count calculated | count=%d",
            result,
        )

        return int(result)

    def average_rating(
        self,
        category=None,
        priority=None,
        status=None,
    ):

        df = self.get_data(category, priority, status)

        ratings = df["customer_rating"].dropna()

        if ratings.empty:
            logger.warning("No customer ratings available")
            return None

        result = round(float(ratings.mean()), 2)

        logger.info(
            "Average rating calculated | rating=%s",
            result,
        )

        return result

    def average_response_time(
        self,
        category=None,
        priority=None,
        status=None,
    ):

        df = self.get_data(category, priority, status)

        result = round(
            float(df["response_time_hrs"].mean()),
            2,
        )

        logger.info(
            "Average response time calculated | hours=%s",
            result,
        )

        return result

    def average_resolution_time(
        self,
        category=None,
        priority=None,
        status=None,
    ):

        df = self.get_data(category, priority, status)

        resolution_times = (
            df["resolution_time_hrs"].dropna()
        )

        if resolution_times.empty:
            logger.warning(
                "No resolution times available"
            )
            return None

        result = round(
            float(resolution_times.mean()),
            2,
        )

        logger.info(
            "Average resolution time calculated | hours=%s",
            result,
        )

        return result

    def count_by_category(self):

        df = load_data()

        result = (
            df["category"]
            .value_counts()
            .to_dict()
        )

        logger.info(
            "Category-wise ticket count calculated"
        )

        return result

    def count_by_priority(self):

        df = load_data()

        result = (
            df["priority"]
            .value_counts()
            .to_dict()
        )

        logger.info(
            "Priority-wise ticket count calculated"
        )

        return result

    def count_by_status(self):

        df = load_data()

        result = (
            df["status"]
            .value_counts()
            .to_dict()
        )

        logger.info(
            "Status-wise ticket count calculated"
        )

        return result

    def count_by_agent(self):

        df = load_data()

        result = (
            df["agent_id"]
            .value_counts()
            .to_dict()
        )

        logger.info(
            "Agent-wise ticket count calculated"
        )

        return result

    def average_rating_by_agent(self):

        df = load_data()

        result = (
            df.groupby("agent_id")["customer_rating"]
            .mean()
            .dropna()
            .round(2)
            .to_dict()
        )

        logger.info(
            "Agent-wise average rating calculated"
        )

        return result


analytics_service = AnalyticsService()