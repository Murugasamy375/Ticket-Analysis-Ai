import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from app.core.logger import logger
from app.tools.ticket_query import ticket_query
from app.tools.analytics import analytics
from app.tools.semantic_search import semantic_search
from app.tools.anomaly_detection import anomaly_detection


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-120b"
)


# --------------------------------------------------
# System Prompt
# --------------------------------------------------

SYSTEM_PROMPT = """
You are an AI assistant for a support ticket analytics system.

Your job is to answer questions about the support ticket dataset
using the available tools.

IMPORTANT TOOL SELECTION RULES:

1. Use semantic_search when the user asks about:
   - issue descriptions
   - customer problems
   - symptoms
   - similar issues
   - meaning-based searches
   - free-text ticket content

2. Use ticket_query when the user explicitly refers to
   structured ticket fields such as:
   - category
   - priority
   - status
   - unresolved tickets

3. NEVER invent structured field values.

Valid categories:
- General
- Billing
- Technical

Valid priorities:
- Low
- Medium
- High
- Critical

Valid statuses:
- Open
- Escalated
- Resolved

For example, if a user says:
"customers are having payment problems"

do NOT assume category="Payments".

Instead, use semantic_search because "payment problems"
describes an issue rather than explicitly naming a dataset category.

4. Use analytics for:
   - counts
   - averages
   - group-by analysis
   - agent statistics
   - category statistics
   - priority statistics
   - status statistics

5. Use anomaly_detection for:
   - unusually long resolution times
   - old unresolved high-priority tickets
   - anomaly-related questions

6. For semantic search, return the relevant retrieved tickets
   and summarize why they match the user's question.

7. Base factual answers only on the dataset and tool results.

8. NEVER invent:
   - SLA rules
   - business rules
   - ticket information
   - categories
   - priorities
   - statuses
   - dates
   - statistics

9. If a tool returns no matching records, clearly say that
   no matching records were found.

10. If a structured query returns many records, do not claim
    that the displayed records represent every matching record
    unless the tool explicitly provides every record.

11. Keep answers concise and directly answer the user's question.

12. Do not expose internal reasoning or chain-of-thought.
"""


# --------------------------------------------------
# LLM Initialization
# --------------------------------------------------

def create_llm() -> ChatGroq:
    """Create and configure the Groq LLM."""

    logger.info(
        "Initializing LLM | provider=Groq | model=%s",
        LLM_MODEL,
    )

    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not configured")
        raise ValueError(
            "GROQ_API_KEY is not configured"
        )

    llm = ChatGroq(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
    )

    logger.info(
        "LLM initialized successfully"
    )

    return llm


llm = create_llm()


# --------------------------------------------------
# Tool Binding
# --------------------------------------------------

TOOLS = [
    ticket_query,
    analytics,
    semantic_search,
    anomaly_detection,
]

llm_with_tools = llm.bind_tools(TOOLS)

logger.info(
    "Tools bound to LLM | tool_count=%d",
    len(TOOLS),
)


# --------------------------------------------------
# Query Execution
# --------------------------------------------------

def run_query(query: str) -> str:
    """
    Process a natural-language support-ticket query.

    The LLM selects the appropriate tool, receives the
    tool result, and generates the final answer.
    """

    logger.info(
        "Processing user query | query=%s",
        query,
    )

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]

    # One tool-calling cycle for the current architecture.
    response = llm_with_tools.invoke(messages)

    # --------------------------------------------------
    # No tool required
    # --------------------------------------------------

    if not response.tool_calls:
        logger.info(
            "No tool call required"
        )

        return response.content

    tool_map = {
        tool.name: tool
        for tool in TOOLS
    }

    tool_messages = []

    # --------------------------------------------------
    # Execute selected tools
    # --------------------------------------------------

    for tool_call in response.tool_calls:

        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.info(
            "Executing tool | name=%s | args=%s",
            tool_name,
            tool_args,
        )

        if tool_name not in tool_map:
            logger.error(
                "Unknown tool requested | tool=%s",
                tool_name,
            )

            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        tool = tool_map[tool_name]

        try:
            tool_result = tool.invoke(
                tool_args
            )

        except Exception:
            logger.exception(
                "Tool execution failed | tool=%s",
                tool_name,
            )
            raise

        logger.info(
            "Tool execution completed | tool=%s",
            tool_name,
        )

        tool_messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"],
            )
        )

    # --------------------------------------------------
    # Generate final answer
    # --------------------------------------------------

    final_messages = [
        *messages,
        response,
        *tool_messages,
    ]

    final_response = llm.invoke(
        final_messages
    )

    logger.info(
        "Final LLM response generated"
    )

    return final_response.content