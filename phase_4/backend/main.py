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

# Global variables to hold components
startup_error = None
chatbot = None
init_scheduler = None
shutdown_scheduler = None

try:
    from phase_3.main_rag import INDMoneyChatbot
    from phase_5.scheduler.manager import init_scheduler, shutdown_scheduler
    HAS_COMPONENTS = True
except Exception as e:
    print(f"CRITICAL ERROR during component import: {e}")
    import traceback
    startup_error = traceback.format_exc()
    traceback.print_exc()
    HAS_COMPONENTS = False

# We will initialize everything on the first request to avoid blocking Uvicorn startup
app = FastAPI(title="INDMoney MF Assistant API")

@app.get("/")
async def root():
    return {"message": "INDMoney Backend is LIVE"}

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# chatbot initialization moved to lifespan

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

@app.get("/debug")
async def get_debug():
    global startup_error
    if startup_error:
        return {"error": startup_error}
    return {"status": "No startup errors detected"}

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
    global chatbot
    if not chatbot and HAS_COMPONENTS:
        print("Lazy loading INDMoney Chatbot... (this may take a moment)")
        chatbot = INDMoneyChatbot()
        
        # Initialize Scheduler here so it doesn't block Uvicorn startup
        print("Starting Phase 5 Data Refresh Scheduler...")
        try:
            if init_scheduler:
                init_scheduler()
                print("Scheduler started.")
        except Exception as e:
            print(f"Error starting scheduler: {e}")
        
    if not chatbot:
        raise HTTPException(status_code=503, detail="AI Chatbot is not initialized (likely due to startup error)")
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Natively bind to 7860 for Hugging Face Spaces compatibility
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
