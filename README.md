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
pip install -r requirements.txt

# Create .env file at the root with your Groq API key
echo GROQ_API_KEY=your_api_key_here > .env
```

### 2. Initial Data Indexing (One-time)
Since the vector database is local, you need to build it once from the processed JSON files:
```bash
py phase_1/chunker.py
```

### 3. Running the Project

**Backend (Terminal 1):**
```bash
py phase_4/backend/main.py
# Backend will run on http://localhost:8000
```

**Frontend (Terminal 2):**
```bash
cd phase_4/frontend
npm install
npm run dev
# Frontend will run on http://localhost:5173
```

**Access the Application:**
Open your browser and navigate to `http://localhost:5173`

### 4. Environment Configuration

The frontend uses environment variables to configure the API URL:

- **Local Development**: Uses `.env.local` (auto-created, points to `http://localhost:8000`)
- **Production**: Uses `.env.production` (points to Railway deployment)

To switch environments:
```bash
# For local development (default)
npm run dev

# For production build
npm run build
```

### 5. Verification
```bash
# Run exhaustive integration tests
py phase_3/test_integration_exhaustive.py

# Test backend API
curl http://localhost:8000/health
```

## Guardrails & Constraints
- **PII Blocking**: Automatically blocks PAN, Aadhaar, phone, and email.
- **No Financial Advice**: Deflects investment recommendations to consult with experts.
- **Strict Formatting**: Max 3 sentences, 1 citation, and source footer.

## Tech Stack
- **Backend**: FastAPI, LangChain, ChromaDB, Groq LLM
- **Frontend**: React, Vite, Lucide Icons
- **Embeddings**: HuggingFace BGE-small-en-v1.5
- **Deployment**: Railway (Backend), Vercel (Frontend)

## Features
- ✅ Real-time mutual fund data retrieval
- ✅ RAG-based accurate responses with citations
- ✅ Fund selector for focused queries
- ✅ Automated daily data refresh (Phase 5)
- ✅ PII protection and guardrails
- ✅ Mobile-responsive UI

## License
MIT License - see LICENSE file for details
