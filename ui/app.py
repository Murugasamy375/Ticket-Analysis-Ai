import requests
import pandas as pd
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="Ticket AI Analytics",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# Custom Styling
# ============================================================

st.markdown(
    """
    <style>

    [data-testid="stSidebar"] {
        display: none;
    }

    [data-testid="stMetricValue"] {
        color: white !important;
    }

    [data-testid="stMetricLabel"] {
        color: white !important;
    }

    .stApp {
        background-color: #0e1117;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API Helper
# ============================================================

def get_api_data(
    endpoint,
    params=None,
):

    try:

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"API connection failed: {e}"
        )

        return None


# ============================================================
# Header
# ============================================================

st.title(
    "🎫 Ticket AI Analytics"
)

st.caption(
    "AI-powered support ticket analytics, "
    "semantic search and anomaly detection"
)


# ============================================================
# Health Check
# ============================================================

health_col1, health_col2 = st.columns(
    [0.25, 0.75]
)

with health_col1:

    health_check = st.button(
        "🩺 Health Check",
        width="stretch",
    )


if health_check:

    health = get_api_data(
        "/health"
    )

    if health:

        if health.get("status") == "healthy":

            st.success(
                f"🟢 System Healthy | "
                f"Dataset: {health.get('rows')} rows | "
                f"LLM: Available"
            )

        else:

            st.error(
                f"🔴 System Unhealthy | "
                f"Dataset loaded: "
                f"{health.get('dataset_loaded')} | "
                f"LLM available: "
                f"{health.get('llm_available')}"
            )


# ============================================================
# Dataset Statistics
# ============================================================

dataset = get_api_data(
    "/dataset"
)


if dataset:

    stats = dataset.get(
        "statistics",
        {}
    )

    total_tickets = dataset.get(
        "total_rows",
        0
    )

    resolved_tickets = stats.get(
        "resolved_tickets",
        0
    )

    unresolved_tickets = stats.get(
        "unresolved_tickets",
        0
    )

    critical_tickets = stats.get(
        "critical_tickets",
        0
    )

else:

    total_tickets = 0
    resolved_tickets = 0
    unresolved_tickets = 0
    critical_tickets = 0


# ============================================================
# Metrics
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        label="Total Tickets",
        value=total_tickets,
    )


with col2:

    st.metric(
        label="Resolved Tickets",
        value=resolved_tickets,
    )


with col3:

    st.metric(
        label="Unresolved Tickets",
        value=unresolved_tickets,
    )


with col4:

    st.metric(
        label="Critical Tickets",
        value=critical_tickets,
    )


# ============================================================
# Ticket Filters
# ============================================================

st.markdown(
    "### 🔎 Filter Tickets"
)


with st.container(border=True):

    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(
        [1, 1, 1, 1, 0.5]
    )

    with filter_col1:

        category = st.selectbox(
            "Category",
            [
                "All",
                "General",
                "Billing",
                "Technical",
            ],
        )

    with filter_col2:

        priority = st.selectbox(
            "Priority",
            [
                "All",
                "Low",
                "Medium",
                "High",
                "Critical",
            ],
        )

    with filter_col3:

        status = st.selectbox(
            "Status",
            [
                "All",
                "Open",
                "Escalated",
                "Resolved",
            ],
        )

    with filter_col4:

        ticket_id = st.text_input(
            "Ticket ID",
            placeholder="e.g. TKT-001",
        )

    with filter_col5:

        st.write("")
        st.write("")

        apply_filter = st.button(
            "Apply",
            width="stretch",
        )


# ============================================================
# Ticket Records + AI Agent
# ============================================================

left_col, right_col = st.columns(
    [1.6, 1]
)


# ============================================================
# Ticket Records
# ============================================================

with left_col:

    st.subheader(
        "🎫 Ticket Records"
    )

    if apply_filter:

        params = {}

        if category != "All":

            params["category"] = category

        if priority != "All":

            params["priority"] = priority

        if status != "All":

            params["status"] = status

        if ticket_id.strip():

            params["ticket_id"] = (
                ticket_id.strip()
            )

        result = get_api_data(
            "/filter",
            params=params,
        )

    else:

        result = get_api_data(
            "/filter"
        )


    if result:

        records = result.get(
            "records",
            []
        )

        st.write(
            f"Showing **{len(records)}** tickets"
        )

        if records:

            # Convert records to DataFrame
            display_df = pd.DataFrame(
                records
            )

            # Keep numeric columns numeric
            numeric_columns = [
                "response_time_hrs",
                "resolution_time_hrs",
                "customer_rating",
            ]

            for column in numeric_columns:

                if column in display_df.columns:

                    display_df[column] = pd.to_numeric(
                        display_df[column],
                        errors="coerce",
                    )

            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "No tickets found for "
                "the selected filters."
            )


# ============================================================
# AI Agent
# ============================================================

with right_col:

    st.subheader(
        "🤖 AI Agent"
    )

    st.write(
        "Ask questions about the "
        "support ticket dataset."
    )

    query = st.text_area(
        "Your question",
        placeholder=(
            "Example: How many critical "
            "tickets are unresolved?"
        ),
        height=150,
    )

    ask_ai = st.button(
        "Ask AI",
        width="stretch",
    )


    if ask_ai:

        if not query.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "AI is analyzing..."
            ):

                try:

                    response = requests.post(
                        f"{API_BASE_URL}/query",
                        json={
                            "query": query
                        },
                        timeout=60,
                    )

                    response.raise_for_status()

                    result = response.json()

                    st.success(
                        result.get(
                            "answer",
                            "No answer returned.",
                        )
                    )

                except requests.exceptions.RequestException as e:

                    st.error(
                        f"AI request failed: {e}"
                    )


# ============================================================
# Anomaly Detection
# ============================================================

st.markdown("---")

st.subheader(
    "🚨 Anomaly Detection"
)

st.write(
    "Detect tickets with unusually long "
    "resolution times and unresolved "
    "high-priority tickets older than "
    "the selected threshold."
)


with st.container(border=True):

    anomaly_col1, anomaly_col2, anomaly_col3 = st.columns(
        [1, 1, 0.7]
    )

    with anomaly_col1:

        resolution_threshold = st.number_input(
            "Long Resolution Threshold (hours)",
            min_value=1.0,
            value=24.0,
            step=1.0,
        )

    with anomaly_col2:

        unresolved_age_threshold = st.number_input(
            "Unresolved High-Priority Age (hours)",
            min_value=1.0,
            value=24.0,
            step=1.0,
        )

    with anomaly_col3:

        st.write("")
        st.write("")

        check_anomalies = st.button(
            "🚨 Detect Anomalies",
            width="stretch",
        )


if check_anomalies:

    try:

        anomaly_response = requests.get(
            f"{API_BASE_URL}/anomalies",
            params={
                "resolution_time_threshold":
                    resolution_threshold,

                "unresolved_age_threshold":
                    unresolved_age_threshold,
            },
            timeout=30,
        )

        anomaly_response.raise_for_status()

        anomaly_data = anomaly_response.json()


        # ----------------------------------------------------
        # Anomaly Metrics
        # ----------------------------------------------------

        anomaly_col1, anomaly_col2, anomaly_col3 = st.columns(
            3
        )


        with anomaly_col1:

            st.metric(
                "Long Resolution Anomalies",
                anomaly_data.get(
                    "long_resolution_count",
                    0,
                ),
            )


        with anomaly_col2:

            st.metric(
                "Old Unresolved High-Priority",
                anomaly_data.get(
                    "old_unresolved_high_priority_count",
                    0,
                ),
            )


        with anomaly_col3:

            st.metric(
                "Total Anomalies",
                anomaly_data.get(
                    "total_anomalies",
                    0,
                ),
            )


        # ----------------------------------------------------
        # Long Resolution Tickets
        # ----------------------------------------------------

        st.markdown(
            "#### ⏱️ Long Resolution Tickets"
        )

        long_resolution = anomaly_data.get(
            "long_resolution_samples",
            [],
        )

        if long_resolution:

            long_df = pd.DataFrame(
                long_resolution
            )

            st.dataframe(
                long_df,
                width="stretch",
                hide_index=True,
            )

        else:

            st.success(
                "No long-resolution anomalies detected."
            )


        # ----------------------------------------------------
        # Old Unresolved High Priority
        # ----------------------------------------------------

        st.markdown(
            "#### 🔴 Old Unresolved High-Priority Tickets"
        )

        old_unresolved = anomaly_data.get(
            "old_unresolved_high_priority_samples",
            [],
        )

        if old_unresolved:

            old_df = pd.DataFrame(
                old_unresolved
            )

            st.dataframe(
                old_df,
                width="stretch",
                hide_index=True,
            )

        else:

            st.success(
                "No old unresolved high-priority "
                "tickets detected."
            )


    except requests.exceptions.RequestException as e:

        st.error(
            f"Anomaly detection request failed: {e}"
        )


# ============================================================
# Footer
# ============================================================

st.markdown("---")

st.caption(
    "Ticket AI Analytics • "
    "FastAPI + Streamlit + Groq + "
    "Sentence Transformers + ChromaDB"
)