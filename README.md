# Ticket AI Analytics

This project is a small AI-powered support ticket analytics application built for the assessment. It combines an LLM with normal Python/Pandas analytics and semantic search so that users can ask questions about the support-ticket CSV in natural language.

It loads a support-ticket CSV, answers natural-language questions, performs exact analytics, searches ticket content semantically, detects anomalies, and exposes everything through a REST API and a minimal web UI.

## 1. What It Does

Examples:

- How many tickets are currently open?
- How many critical tickets are unresolved?
- What is the average customer rating for Technical tickets?
- Which agent resolved the most tickets?
- Show tickets related to payment problems.
- Find old unresolved high-priority tickets.

The **LLM understands the question and selects a tool**. Python/Pandas performs exact calculations; RAG handles meaning-based ticket searches.

## 2. Architecture

```text
User
  |
  +--> Streamlit UI
  |       |
  +--> FastAPI /docs
          |
        /query
          |
       Groq LLM
          |
   LangChain Tool Calling
          |
   +------+------+------+------+
   |             |             |
ticket_query  analytics  semantic_search  anomaly_detection
   |             |             |             |
 Pandas        Pandas      Embeddings     Pandas
                           + ChromaDB
```

### Hybrid approach

- **Pandas**: exact counts, filters, averages, grouping.
- **ChromaDB + SentenceTransformers**: semantic/free-text retrieval.
- **Groq LLM**: question understanding, tool selection, final answer.

RAG is not used for exact calculations because vector retrieval is not guaranteed to produce dataset-wide counts or averages.

## 3. Main Tools

### `ticket_query`

Structured filters:

- category: General, Billing, Technical
- priority: Low, Medium, High, Critical
- status: Open, Escalated, Resolved
- unresolved

Example:

```text
How many critical tickets are unresolved?
```

The tool normally returns only a count. Explicit record-list requests are limited to 20 records before passing them to the LLM.

### `analytics`

Supports:

- counts
- resolved/unresolved counts
- average customer rating
- average response/resolution time
- counts by category/priority/status/agent
- average rating by agent

Example:

```text
What is the average customer rating for Technical category tickets?
```

### `semantic_search`

Used for meaning-based questions:

```text
Show tickets related to payment problems.
Find tickets where customers have login problems.
Show issues similar to billing failures.
```

Pipeline:

```text
Question
  ↓
SentenceTransformer
  ↓
Embedding
  ↓
ChromaDB
  ↓
Relevant ticket records
  ↓
Groq summary
```

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Each ticket is stored as one complete document containing its fields and issue summary. No recursive text splitting is required because one CSV row is already a self-contained ticket.

### `anomaly_detection`

Two rules are implemented:

1. Resolved tickets where `resolution_time_hrs > threshold`.
2. Unresolved High/Critical tickets older than the configured age threshold.

Default threshold:

```text
24 hours
```

For this dataset, ticket age is calculated relative to the latest `created_at` value in the dataset.

## 4. Dataset

File:

```text
data/support_tickets.csv
```

Columns:

```text
ticket_id
created_at
category
priority
status
response_time_hrs
resolution_time_hrs
agent_id
customer_rating
issue_summary
```

Provided dataset:

```text
500 tickets
327 resolved
173 unresolved
```

## 5. Project Structure

```text
ticket-ai-analytics/
├── data/
│   └── support_tickets.csv
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   ├── services/
│   │   ├── data_service.py
│   │   ├── analytics_service.py
│   │   ├── rag_service.py
│   │   └── anomaly_service.py
│   ├── tools/
│   │   ├── ticket_query.py
│   │   ├── analytics.py
│   │   ├── semantic_search.py
│   │   └── anomaly_detection.py
│   ├── rag/
│   │   └── rag.py
│   └── llm/
│       └── llm.py
├── ui/
│   └── app.py
├── logs/
├── chroma_db/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
main.py
```

## 6. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application |
| FastAPI | REST API |
| Uvicorn | Server |
| Streamlit | UI |
| Groq | LLM |
| LangChain | Tool calling |
| Pandas | Analytics |
| ChromaDB | Vector database |
| SentenceTransformers | Embeddings |
| Pydantic | Validation |
| python-dotenv | Configuration |
| Logging | Logs |

## 7. Setup

### Create virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create `.env`

```env
APP_NAME=Ticket AI Analytics
ENVIRONMENT=development
DATA_PATH=data/support_tickets.csv
GROQ_API_KEY=YOUR_GROQ_API_KEY
LLM_MODEL=openai/gpt-oss-120b
API_BASE_URL=http://127.0.0.1:8000
```

Do not commit `.env`.

## 8. Start the Application

Run this from the project root:

```bash
uvicorn main:app
```

You do not need to start Streamlit separately. FastAPI starts the Streamlit UI automatically.

After the application starts, use these URLs:

```text
API:
http://127.0.0.1:8000

Swagger API documentation:
http://127.0.0.1:8000/docs

FINAL UI VIEWING URL:
http://127.0.0.1:8501
```

**Important: `http://127.0.0.1:8501` is the final UI viewing URL.**

This is the URL to open in the browser when you want to actually use and demonstrate the application.

The `/docs` URL is only for testing and demonstrating the REST API through Swagger.

## 9. End-to-End UI Flow

### Step 1 — Open the UI

Open the **final UI viewing URL**:

```text
http://127.0.0.1:8501
```

This is the main URL for viewing and demonstrating the finished application.

You will see:

```text
Ticket AI Analytics

[ Health Check ]

Total Tickets | Resolved | Unresolved | Critical

Filter Tickets
[Category] [Priority] [Status] [Ticket ID] [Apply]

Ticket Records              AI Agent
```

### Step 2 — Health Check

Click:

```text
🩺 Health Check
```

The UI calls:

```text
GET /health
```

It checks:

- dataset loaded
- number of rows
- LLM configuration available

### Step 3 — View KPIs

The UI calls:

```text
GET /dataset
```

and displays:

```text
Total Tickets
Resolved Tickets
Unresolved Tickets
Critical Tickets
```

### Step 4 — Filter Tickets

The filter section supports four optional filters:

```text
Category
Priority
Status
Ticket ID
```

You can use them individually or combine them. For example, enter:

```text
Ticket ID = TKT-001
```

and click:

```text
Apply
```

The UI calls:

```text
GET /filter?ticket_id=TKT-001
```

The backend performs the filtering using Pandas and returns the matching ticket records.

You can also combine filters, for example:

```text
Priority = Critical
Status = Escalated
Ticket ID = TKT-002
```

If no ticket matches the selected filters, the UI displays:

```text
No tickets found for the selected filters.
```

Ticket ID matching is case-insensitive.

### Step 5 — Ask AI

In the **AI Agent** box enter:

```text
How many critical tickets are unresolved?
```

Click:

```text
Ask AI
```

The UI sends:

```http
POST /query
```

with:

```json
{
  "query": "How many critical tickets are unresolved?"
}
```

The flow is:

```text
UI
 ↓
FastAPI /query
 ↓
Groq LLM
 ↓
ticket_query
 ↓
Pandas
 ↓
Exact count
 ↓
Groq LLM
 ↓
Final answer
 ↓
UI
```

Try:

```text
How many tickets are currently open?
```

```text
What is the average customer rating for Technical category tickets?
```

```text
Which agent resolved the most tickets?
```

```text
Show tickets related to payment problems.
```

## 10. REST API Endpoint Summary

The application exposes the following REST endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application and service information |
| GET | `/health` | Dataset and LLM health status |
| GET | `/dataset` | Dataset metadata and statistics |
| GET | `/filter` | Filter tickets by category, priority, status, and/or Ticket ID |
| POST | `/query` | Natural-language AI query using the LLM and tools |
| GET | `/anomalies` | Detect long-resolution and old unresolved high-priority tickets |

All endpoints are available through Swagger at:

```text
http://127.0.0.1:8000/docs
```

## 11. Anomaly Detection in the UI

The dashboard includes a dedicated **🚨 Anomaly Detection** section below the ticket table and AI Agent.

It provides two configurable thresholds:

```text
Long Resolution Threshold (hours)
Unresolved High-Priority Age (hours)
```

Default values are:

```text
24 hours
24 hours
```

Click:

```text
🚨 Detect Anomalies
```

The UI calls:

```text
GET /anomalies
```

The dashboard then displays:

```text
Long Resolution Anomalies
Old Unresolved High-Priority
Total Anomalies
```

It also displays up to five sample records for each anomaly category.

The backend currently detects:

1. Resolved tickets where `resolution_time_hrs` is greater than the configured threshold.
2. Unresolved High or Critical tickets whose age is greater than the configured threshold.

For unresolved ticket age, the current implementation uses the latest `created_at` timestamp in the dataset as the reference time.

With the default 24-hour thresholds, the tested dataset produced:

```text
Long resolution anomalies: 74
Old unresolved high-priority anomalies: 80
Total anomaly flags: 154
```

## 12. Swagger UI — Exactly Where to Click

Open:

```text
http://127.0.0.1:8000/docs
```

You will see the FastAPI Swagger page.

For each endpoint:

```text
Click endpoint
   ↓
Click "Try it out"
   ↓
Enter parameters/body if required
   ↓
Click "Execute"
   ↓
Read "Response body"
```

### `GET /`

Click:

```text
GET /
→ Try it out
→ Execute
```

Shows application information.

### `GET /health`

Click:

```text
GET /health
→ Try it out
→ Execute
```

Expected fields:

```json
{
  "status": "healthy",
  "application": "Ticket AI Analytics",
  "environment": "development",
  "dataset_loaded": true,
  "rows": 500,
  "llm_available": true
}
```

### `GET /dataset`

Click:

```text
GET /dataset
→ Try it out
→ Execute
```

Returns dataset metadata and statistics.

### `GET /filter`

Click:

```text
GET /filter
→ Try it out
```

The endpoint supports these optional query parameters:

```text
category
priority
status
ticket_id
```

Example:

```text
category = Technical
priority = Critical
status = Escalated
ticket_id = TKT-002
```

Then:

```text
Execute
```

The response contains:

```json
{
  "count": 1,
  "records": [
    {
      "ticket_id": "TKT-002"
    }
  ]
}
```

The actual result depends on the selected filters. Leave all parameters empty to retrieve all records.

Ticket ID matching is case-insensitive.

### `POST /query`

Click:

```text
POST /query
→ Try it out
```

Replace the request body with:

```json
{
  "query": "How many critical tickets are unresolved?"
}
```

Then:

```text
Execute
```

Response:

```json
{
  "query": "How many critical tickets are unresolved?",
  "answer": "..."
}
```

Try:

```json
{
  "query": "Show tickets related to payment problems."
}
```

This demonstrates semantic RAG retrieval.

### `GET /anomalies`

Click:

```text
GET /anomalies
→ Try it out
→ Execute
```

Default parameters:

```text
resolution_time_threshold = 24
unresolved_age_threshold = 24
```

You can change them.

Example:

```text
resolution_time_threshold = 12
```

Then click:

```text
Execute
```

The response contains:

```text
long_resolution_count
old_unresolved_high_priority_count
total_anomalies
long_resolution_samples
old_unresolved_high_priority_samples
```

## 13. Complete AI Request Flow

### Structured question

```text
"How many critical tickets are unresolved?"
          ↓
       Groq LLM
          ↓
     ticket_query
          ↓
        Pandas
          ↓
     Exact count
          ↓
       Groq LLM
          ↓
      Final answer
```

### Analytics question

```text
"What is the average rating for Technical tickets?"
          ↓
       Groq LLM
          ↓
       analytics
          ↓
        Pandas
          ↓
       Average
          ↓
       Groq LLM
          ↓
      Final answer
```

### Semantic question

```text
"Show tickets related to payment problems."
          ↓
       Groq LLM
          ↓
   semantic_search
          ↓
 SentenceTransformer
          ↓
      ChromaDB
          ↓
 Relevant tickets
          ↓
       Groq LLM
          ↓
      Final answer
```

### Anomaly question

```text
"Find old unresolved high-priority tickets."
          ↓
       Groq LLM
          ↓
 anomaly_detection
          ↓
        Pandas
          ↓
     Anomaly rules
          ↓
       Results
          ↓
       Groq LLM
          ↓
      Final answer
```

## 14. Logging

Application logs:

```text
logs/app.log
```

Errors:

```text
logs/error.log
```

Logs include startup, dataset loading, API requests, tool calls, semantic searches, anomaly detection, and exceptions.

## 15. Validation

The dataset loader checks:

- file existence
- required columns
- date parsing

Pydantic validates API requests. `/query` accepts a question between 3 and 500 characters, and anomaly thresholds must be greater than zero.

## 16. Design Decisions

### Why Pandas?

For deterministic and exact dataset calculations.

### Why RAG?

For free-text and meaning-based ticket questions.

### Why ChromaDB?

Local vector storage without a paid external database.

### Why SentenceTransformers?

Lightweight local embeddings suitable for this dataset.

### Why LangChain?

Provides structured LLM tool calling.

### Why Groq?

Provides the LLM API used by the assessment implementation.

### Why not use RAG for counts?

Retrieval returns relevant documents; it does not guarantee an exact dataset-wide aggregation. Pandas is therefore used for exact statistics.

### Why no text splitter?

Each CSV row is already a complete ticket document.

## 17. Limitations

- CSV is used instead of a production database.
- Semantic results depend on embedding quality.
- Record lists passed to the LLM are limited to prevent oversized requests.
- Current execution is a tool-calling flow, not a multi-step LangGraph workflow.
- Anomaly ticket age uses the latest dataset timestamp as the reference point.

## 18. Future Improvements

- PostgreSQL/production database
- Authentication
- More anomaly rules
- Automated evaluation
- Caching
- Production observability
- Docker deployment
- Multi-step orchestration with LangGraph

## 19. Recommended Demo Order

For the assessment walkthrough:

1. Run `uvicorn main:app`
2. Open the **final UI viewing URL**: `http://127.0.0.1:8501`
3. Click **Health Check**
4. Explain the KPI cards
5. Apply a ticket filter
6. Ask a structured AI question
7. Ask an analytics question
8. Ask a semantic/RAG question
9. Open `http://127.0.0.1:8000/docs`
10. Demonstrate `GET /anomalies`
11. Explain the architecture and why Pandas + RAG are combined

## 20. One-Line Summary

**Ticket AI Analytics is a hybrid AI support-ticket analytics system where an LLM understands natural-language questions and routes them to deterministic Pandas analytics, semantic RAG retrieval, or anomaly detection through FastAPI and Streamlit.**
