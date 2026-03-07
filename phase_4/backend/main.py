import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Add project root to sys.path to import phase_3 modules
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from contextlib import asynccontextmanager
from phase_3.main_rag import INDMoneyChatbot
from phase_5.scheduler.manager import init_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize scheduler
    print("DEBUG: Starting Phase 5 Data Refresh Scheduler...")
    init_scheduler()
    yield
    # Shutdown: Stop scheduler
    print("DEBUG: Shutting down Phase 5 Scheduler...")
    shutdown_scheduler()

app = FastAPI(title="INDMoney MF Assistant API", lifespan=lifespan)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Chatbot
chatbot = INDMoneyChatbot()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    answer: str
    citation_url: Optional[str] = None
    footer: str = "Last updated from sources"

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/welcome")
async def get_welcome():
    return {
        "message": "Welcome to INDMoney Mutual Fund Assistant! I can help you with factual information about mutual funds.",
        "examples": [
            "What is the expense ratio of HDFC Mid Cap mutual fund?",
            "What are the minimum SIP amounts?",
            "How do I download my capital gains statement?"
        ],
        "note": "Facts-only. No investment advice."
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # The main_rag.py INDMoneyChatbot.ask handles guardrails and llm generation
        response_text = chatbot.ask(request.message)
        
        # Parse the response to extract citation if possible
        # Our LLM engine usually formats it as: "Answer... [Source](URL)\n\nFooter"
        # We want to separate the answer from the citation for the UI cards
        
        answer = response_text
        citation_url = None
        
        if "[Source](" in response_text:
            parts = response_text.split("[Source](")
            answer = parts[0].strip()
            citation_url = parts[1].split(")")[0]
            
        # Remove the footer if it's already in the response_text to avoid duplication in UI
        if "Last updated from sources" in answer:
            answer = answer.replace("Last updated from sources", "").strip()

        return ChatResponse(
            answer=answer,
            citation_url=citation_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
