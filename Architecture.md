# INDMoney RAG Chatbot — Refined Phase-wise Architecture

> **Version:** 2.0 | **Status:** In Progress | **Scope:** 5 Mutual Funds on INDMoney

---

## Goal Description

Build a production-grade RAG (Retrieval-Augmented Generation) chatbot that accurately answers factual queries about 5 specific mutual funds sourced from INDMoney. The chatbot must handle questions on:

- Expense Ratio
- ELSS Lock-in Period
- Minimum SIP Amount
- Exit Load
- Riskometer & Benchmark Index
- How to Download Capital Gains Statement

**Target Funds:**

| # | Fund Name | Category |
|---|-----------|----------|
| 1 | HDFC Mid Cap Fund — Direct Plan — Growth | Mid Cap |
| 2 | HDFC Flexi Cap Fund — Direct Plan — Growth | Flexi Cap |
| 3 | Aditya Birla Sun Life Quant Fund Direct Growth | Quant |
| 4 | Aditya Birla Sun Life ELSS Tax Saver Fund | ELSS |
| 5 | Edelweiss Nifty Next 50 Index Fund Direct Growth | Index |

---

## High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE (Phase 4)                    │
│              Streamlit / Gradio / FastAPI + React                    │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ User Query
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE (Phase 2 & 3)                    │
│  Query Embedding → Vector Search → Context Retrieval → LLM Prompt   │
└──────┬─────────────────────┬────────────────────────────┬────────────┘
       │                     │                            │
       ▼                     ▼                            ▼
┌─────────────┐   ┌───────────────────┐     ┌────────────────────────┐
│  Embedding  │   │   Vector Store    │     │      LLM Engine        │
│  Model      │   │ ChromaDB / FAISS  │     │  OpenAI / Claude /     │
│ BGE / OpenAI│   │  + Metadata Index │     │  Groq Llama3           │
└─────────────┘   └───────────────────┘     └────────────────────────┘
                             ▲
                             │ Indexed Chunks
                             │
┌──────────────────────────────────────────────────────────────────────┐
│                   DATA INGESTION PIPELINE (Phase 1)                  │
│   Scraper → Parser → Cleaner → Chunker → Embedder → Vector Store    │
└──────────────────────────────────────────────────────────────────────┘
                             ▲
                             │
              ┌──────────────┴──────────────┐
              │   INDMoney Fund Pages (5)    │
              │   https://indmoney.com/mf    │
              └─────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Scraping | `Playwright` + `BeautifulSoup4` | JS-rendered pages require headless browser |
| Data Storage | JSON + Markdown files | Human-readable, version-controllable raw data |
| Chunking | LangChain `RecursiveCharacterTextSplitter` | Preserves semantic boundaries |
| Embeddings | `BAAI/bge-small-en-v1.5` (HuggingFace) | Free, high-quality, ~133MB |
| Vector DB | **ChromaDB** (local) | Persistent, metadata-filterable, no infra cost |
| LLM | `claude-3-haiku` or `gpt-3.5-turbo` | Fast, affordable, strong instruction-following |
| Orchestration | **LangChain** | Chains, memory, retriever abstractions |
| UI | **Streamlit** | Rapid prototyping, Python-native |
| API (optional) | **FastAPI** | Async, lightweight REST layer |
| Evaluation | **RAGAS** | RAG-specific metrics (faithfulness, relevancy) |

---

## Phase 1: Data Ingestion & Processing

**Goal:** Extract, clean, structure, and vectorize data for all 5 target funds.

### 1.1 Web Scraping Strategy

**Scraper Choice:** Use `Playwright` (Python) since INDMoney uses React/dynamic rendering.

```
Target URLs (per fund):
  https://www.indmoney.com/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-growth
  https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-growth
  ... (one URL per fund)
```

**Scraping Steps:**
1. Launch headless Chromium via `playwright.async_api`
2. Wait for key DOM elements to load (e.g., `.fund-details-table`, `#expense-ratio`)
3. Extract raw HTML of the complete fund detail page
4. Save full HTML snapshot to `/data/raw/<fund_slug>.html` as a cache layer
5. Handle rate limiting: add `asyncio.sleep(2–4s)` between requests; rotate User-Agent headers

**Fallback:** If Playwright is blocked, use INDMoney's unofficial API endpoints (`/api/v1/mutual-funds/...`) discovered via browser DevTools network inspection.

### 1.2 Data Extraction & Parsing

Use `BeautifulSoup4` to parse saved HTML snapshots into structured data.

**Fields to extract per fund:**

| Field | HTML Selector (indicative) | Data Type |
|-------|-----------------------------|-----------|
| Fund Name | `h1.fund-name` | string |
| Expense Ratio | `.expense-ratio-value` | float (%) |
| Exit Load | `.exit-load-details` | string |
| Minimum SIP | `.sip-min-amount` | int (₹) |
| Lock-in Period | `.lock-in-period` | string (ELSS only) |
| Benchmark | `.benchmark-name` | string |
| Riskometer Level | `.risk-label` | string |
| Fund Category | `.fund-category` | string |
| AUM | `.aum-value` | float (₹ Cr) |
| NAV | `.nav-value` | float |
| Fund Manager | `.fund-manager-name` | string |
| Fund Description | `.fund-overview-text` | string (long text) |
| Capital Gains Help | Static content (hardcoded or scraped from help section) | string |

**Output:** Save each fund's data as `/data/processed/<fund_slug>.json`

```json
{
  "fund_name": "HDFC Mid Cap Fund - Direct Plan - Growth",
  "fund_slug": "hdfc-mid-cap-fund",
  "source_url": "https://www.indmoney.com/...",
  "scraped_at": "2025-01-01T10:00:00Z",
  "data": {
    "expense_ratio": "0.72%",
    "exit_load": "1% if redeemed within 1 year",
    "minimum_sip": 100,
    "lock_in_period": "N/A",
    "benchmark": "Nifty Midcap 150 TRI",
    "risk_level": "Very High",
    "fund_description": "...",
    "capital_gains_download": "Go to INDMoney App > Portfolio > Mutual Funds > Reports > Capital Gains Statement"
  }
}
```

### 1.3 Document Chunking Strategy

Convert structured JSON fields into natural language passages before chunking — this improves semantic retrieval over raw JSON.

**Template for generating text passages (per fund):**
```
"{fund_name} has an expense ratio of {expense_ratio}. 
The exit load is {exit_load}. The minimum SIP is ₹{minimum_sip}.
The fund benchmarks against {benchmark} and carries a {risk_level} risk."
```

**Chunking Configuration:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,          # ~300–400 tokens per chunk
    chunk_overlap=60,        # Preserve context across boundaries
    separators=["\n\n", "\n", ". ", " "]
)
```

**Chunking rules:**
- Keep atomic facts (e.g., "expense ratio = 0.72%") in the same chunk — never split mid-sentence
- Each chunk must carry full metadata (fund name, category, field type)
- Generate 1 dedicated chunk per key field (expense ratio, exit load, etc.) in addition to free-text chunks — this guarantees retrieval of structured facts

**Expected chunk count:** ~15–25 chunks per fund → ~75–125 total chunks across 5 funds

### 1.4 Embedding Generation

```python
from langchain.embeddings import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}   # Cosine similarity ready
)
```

**Alternative (if higher accuracy needed):** `BAAI/bge-large-en-v1.5` or OpenAI `text-embedding-3-small`

### 1.5 Vector Database — ChromaDB Setup

```python
import chromadb
from langchain.vectorstores import Chroma

# Persistent store — survives restarts
chroma_client = chromadb.PersistentClient(path="./data/vectorstore")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    collection_name="indmoney_mf_rag",
    client=chroma_client
)
```

**Metadata schema per chunk:**
```python
{
  "fund_name": "HDFC Mid Cap Fund",
  "fund_slug": "hdfc-mid-cap-fund",
  "category": "Mid Cap",
  "field_type": "expense_ratio",   # Enables precise metadata filtering
  "source_url": "https://...",
  "scraped_at": "2025-01-01"
}
```

**Re-ingestion strategy:** Track a `content_hash` (SHA-256 of raw text) per chunk — skip re-embedding if hash is unchanged; only re-embed stale or updated chunks.

---

## Phase 2: RAG Pipeline Setup & Retrieval

**Goal:** Accurately retrieve the most relevant context chunks given a user query.

### 2.1 Query Understanding & Pre-processing

Before embedding the raw query, apply these pre-processing steps:

1.  **Fund Name Resolution:** Map informal fund references to canonical slugs
    -   e.g., "HDFC mid cap" → `hdfc-mid-cap-fund`
    -   Use fuzzy matching (`rapidfuzz` library, threshold: 85%)
2.  **Intent Detection (lightweight):** Classify query intent to assist metadata filtering
    -   Categories: `expense_ratio`, `exit_load`, `sip`, `lock_in`, `risk`, `capital_gains`, `general`
    -   Method: simple keyword matching (no LLM needed at this stage)
3.  **Query Expansion (optional):** Append synonyms to improve recall
    -   e.g., "TER" → "TER expense ratio total expense ratio"

### 2.2 Hybrid Retrieval

Use **Hybrid Search** (dense + sparse) for better recall:

```
Query
  │
  ├── Dense Retrieval (Semantic) ──► ChromaDB cosine similarity (Top-8)
  │
  └── Sparse Retrieval (Keyword) ──► BM25 over chunked corpus (Top-8)
                                              │
                                    Reciprocal Rank Fusion (RRF)
                                              │
                                    Re-ranked Top-K=5 chunks
```

**Implementation:**
```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever

bm25_retriever = BM25Retriever.from_documents(chunks, k=8)
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, dense_retriever],
    weights=[0.4, 0.6]   # Weight semantic search higher
)
```

### 2.3 Metadata Filtering

Apply pre-filters before similarity search to boost precision:

```python
# Example: User asks about HDFC Mid Cap expense ratio
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 5,
        "filter": {
            "fund_slug": "hdfc-mid-cap-fund",   # Resolved from query
            "field_type": "expense_ratio"        # Resolved from intent
        }
    }
)
```

**Fallback:** If metadata-filtered results return < 2 chunks, fall back to unfiltered semantic search across all 5 funds.

### 2.4 Retrieval Quality Guardrails

- **Minimum similarity threshold:** Reject chunks with cosine similarity < 0.55 to avoid injecting irrelevant context
- **Maximum context window:** Cap total retrieved text at 2,000 tokens before passing to LLM
- **Deduplication:** Remove near-duplicate chunks (similarity > 0.97) before building the context

---

## Phase 3: LLM Integration & Answer Generation

**Goal:** Generate accurate, grounded, cited answers using retrieved context and Groq LLM.

### 3.1 LLM Configuration

**Engine:** **Groq** exclusively (recommended: `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`).

```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,          # Zero temperature — factual queries only
    max_tokens=512,
    api_key=os.getenv("GROQ_API_KEY")
)
```

**Why Groq:** Extreme speed (low latency) and strong performance on reasoning/instruction-following.

### 3.2 Groundedness & Strict Constraints

The chatbot must act as a restricted factual assistant.

*   **No Self-Answering:** Do NOT use internal model knowledge. Answer ONLY using information from the provided retrieved context.
*   **Conciseness:** Answers must be helpful but restricted to **maximum 3 sentences**.
*   **Citations:** Every answer must include exactly **one clear citation link** to the source page on INDMoney.
*   **Privacy (PII):** Strictly do NOT accept or store PII (PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers).
*   **Anti-Advice:** Refuse any opinionated or portfolio questions (e.g., "Should I buy/sell?", "Is this a good fund?") with a polite message: *"I can only provide factual data about these mutual funds. For investment advice, please consult a SEBI-registered advisor."* Include a relevant educational link.
*   **Performance:** Do not compute or compare returns. If asked for performance analysis, provide a link to the official fund factsheet.
*   **Sources:** Use public INDMoney sources only. No third-party blogs or private backend screenshots.
*   **Transparency:** Every response must end with the footer: *"Last updated from sources"*.

### 3.3 Prompt Engineering

**System Prompt:**
```
You are an expert mutual fund assistant for INDMoney.
Your ONLY job is to answer questions about the 5 specific mutual funds provided in the context.

STRICT RULES:
1. Answer ONLY using the provided CONTEXT. If not present, say: "I don't have that information. Please check indmoney.com."
2. Never provide investment advice or opinions (Buy/Sell/Hold).
3. Do not compute or compare returns.
4. Maximum 3 sentences per answer.
5. Include exactly ONE citation link from metadata.
6. End every answer with: "\n\nLast updated from sources"
7. Do NOT process PII (PAN, Aadhaar, etc.).
```

### 3.4 Response Synthesis

The output must be a clean, cited response verified against the context for groundedness.

---


## Phase 4: Decoupled Web Application (FastAPI + React/Next.js)

**Goal:** Build a production-grade web application with a separate frontend and backend for high performance and scalability.

### 4.1 Backend: RAG API (FastAPI)
The Python backend acts as the brain, exposing the RAG pipeline via REST endpoints.
- **Tech Stack:** FastAPI, Pydantic, Uvicorn.
- **Key Responsibilities:**
    - Receive user queries and apply Phase 2/3 guardrails (PII/Advice).
    - Orchestrate retrieval from ChromaDB.
    - Generate cited responses using Groq LLM.
    - welcome line + 3 example questions and a note: “Facts-only. No investment advice.”
    - Show only one clear citation link in every answer


### 4.2 Frontend: Chat UI (React / Next.js)
A premium, responsive interface for a seamless user experience.
- **Tech Stack:** Next.js (App Router), TailwindCSS (or Vanilla CSS for maximum polish), Lucide-React.
- **Features:**
    - **Modern interface:** Glassmorphism, smooth animations, and clean typography.
    - **Contextual UI:** Displaying citations as clickable cards or refined links.
    - **Error Handling:** Graceful handling of API timeouts or empty results.
- **Aesthetics:** High-contrast, premium dark/light mode inspired by modern fintech apps.

---

## Phase 5: Automated Data Refresh Scheduler

**Goal:** Ensure the chatbot always has the latest NAV, returns, and fund factsheet data by automating the ingestion pipeline.

### 5.1 Technical Architecture
- **Scheduler Engine:** `APScheduler` (Advanced Python Scheduler) integrated into the FastAPI backend.
- **Task Frequency:** 12:00 AM (Midnight) daily.
- **Workflow:**
    1. **Trigger:** Scheduler fires at midnight.
    2. **Scraping:** Execute `Phase 1` scraper to fetch fresh HTML/JSON from INDMoney.
    3. **Processing:** Parse and compare new data with existing records.
    4. **Vector Sync:** 
        - Identify changed data points.
        - Delete old embeddings for the specific `fund_id` and `field_type`.
        - Re-embed new chunks and insert into ChromaDB.
    5. **Logging:** Log success/failure metrics to `refresh_logs/`.

### 5.2 Implementation Components
- **`scheduler/manager.py`:** Central registry for background jobs.
- **`scheduler/tasks.py`:** Wrapper functions for scraping and re-indexing.
- **`backend/main.py`:** Hook to initialize the scheduler on app startup.

### 5.3 Reliability & Safety
- **Retry Logic:** Exponential backoff if INDMoney is unreachable.
- **Data Integrity:** Validate new JSON schema before overwriting vector store.
- **Alerts:** (Optional) Notify via email/webhook if refresh fails 3 times consecutively.

---

## Phase 6: Monitoring & Evaluation *(Deferred)*

**Goal:** Ensure reliability and scale the chatbot.
- **RAGAS Evaluation:** Automated metrics for faithfulness and context precision.
- **Observability:** logging traces via LangSmith or standard structured logs.

## Evaluation Framework

### Offline Evaluation (RAGAS)

Build a golden Q&A dataset of ~30 question–answer pairs (6 per fund) covering all key fields. Run RAGAS metrics after each pipeline change:

| Metric | Description | Target |
|--------|-------------|--------|
| **Faithfulness** | Answer grounded in retrieved context | > 0.90 |
| **Answer Relevancy** | Answer addresses the question | > 0.85 |
| **Context Precision** | Retrieved chunks are relevant | > 0.80 |
| **Context Recall** | All relevant info is retrieved | > 0.75 |

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

results = evaluate(
    dataset=golden_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)
```

### Online Evaluation (Post-deployment)

- **Thumbs up/down** feedback button on each response
- Log all low-confidence responses (< 3 retrieved chunks) for manual review
- Weekly audit of 20 random queries by a human reviewer

---

## Project Directory Structure

```
indmoney-rag-chatbot/
├── data/
│   ├── raw/                     # HTML snapshots from scraper
│   ├── processed/               # Structured JSON per fund
│   └── vectorstore/             # ChromaDB persistent storage
├── src/
│   ├── ingestion/
│   │   ├── scraper.py           # Playwright scraper
│   │   ├── parser.py            # BeautifulSoup parser
│   │   └── chunker.py           # Text splitter + embedder
│   ├── retrieval/
│   │   ├── retriever.py         # Hybrid retriever setup
│   │   └── query_processor.py   # Fund resolution + intent detection
│   ├── generation/
│   │   ├── llm.py               # LLM client + prompt templates
│   │   └── guardrails.py        # Post-generation checks
│   ├── memory/
│   │   └── session_memory.py    # Conversational buffer memory
│   └── api/
│       └── main.py              # FastAPI app (optional)
├── app.py                       # Streamlit UI entry point
├── eval/
│   ├── golden_dataset.json      # Ground truth Q&A pairs
│   └── run_eval.py              # RAGAS evaluation script
├── tests/
│   ├── test_scraper.py
│   ├── test_retriever.py
│   └── test_generation.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| INDMoney blocks scraper | Medium | High | Cache HTML; use polite crawl delays; fallback to API |
| LLM hallucination on numbers | Medium | High | Temperature=0; numeric consistency check; RAGAS eval |
| Stale fund data | Medium | Medium | Weekly scheduled re-scraping job |
| ChromaDB data loss | Low | High | Daily backup of `/data/vectorstore` to cloud storage |
| Out-of-scope queries flooding | High | Low | Strict system prompt + fund list guardrail pre-check |
| Embedding model deprecation | Low | Medium | Abstract embedding layer; swap model in one config line |

---

*Last updated: 2025 | Architecture owner: Engineering Team*
