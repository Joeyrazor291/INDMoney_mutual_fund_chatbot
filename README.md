# INDmoney Mutual Fund RAG Chatbot

A high-fidelity Retrieval-Augmented Generation (RAG) chatbot focused on providing factual mutual fund data sourced from INDmoney and MFAPI.

## Project Structure

This project is organized into autonomous phases for ingestion, retrieval, and UI:

- **phase_1/**: Data Ingestion (Scraping INDmoney HTML, fetching MFAPI NAVs, Parser, Chunker)
- **phase_2/**: Retrieval Layer (Query Processor, Vector Store Search)
- **phase_3/**: LLM & Guardrails (Integrity checks, PII blocking, Citation formatting)
- **phase_4/**: Frontend & Backend (FastAPI Server, Vite/React UI with Fund Selector)
- **phase_5/**: Automation (Task Scheduler for daily data refresh)
- **data/**: Local data storage (Raw HTML, Processed JSON, ChromaDB Vector Store)

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Backend Setup
```bash
# Install dependencies
pip install -r phase_4/backend/requirements.txt

# Create .env file at the root
# Add: GROQ_API_KEY=your_api_key_here
```

### 2. Initial Data Indexing (One-time)
Since the vector database is local, you need to build it once from the processed JSON files:
```bash
py phase_1/chunker.py
```

### 3. Running the Project
**Backend:**
```bash
py phase_4/backend/main.py
```

**Frontend:**
```bash
cd phase_4/frontend
npm install
npm run dev
```

### 3. Verification
```bash
# Run exhaustive integration tests
py phase_3/test_integration_exhaustive.py
```

## Guardrails & Constraints
- **PII Blocking**: Automatically blocks PAN, Aadhaar, phone, and email.
- **No Financial Advice**: Deflects investment recommendations to consult with experts.
- **Strict Formatting**: Max 3 sentences, 1 citation, and source footer.
