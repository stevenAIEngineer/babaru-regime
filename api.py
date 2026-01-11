# Author: Steven Lansangan
# Simple API wrapper
# This is what connects to the internet
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
import os

import base64
from backend import babaru_brain
from utils import memory_manager, voice_manager

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Babaru Cloud API", version="1.0.0")

# Allow requests from anywhere (for testing)
# This fixes the CORS error when we use local html files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: Optional[str] = "CONTEXT_GENERAL"

class ChatResponse(BaseModel):
    response: str
    audio_base64: Optional[str] = None # Added for audio data
    
@app.on_event("startup")
async def startup_event():
    memory_manager.init_db()

@app.get("/")
def read_root():
    return {"status": "Babaru is watching you.", "version": "1.0.0"}

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to Babaru
    """
    try:
        # Pass to Brain
        ai_reply = babaru_brain.get_response(
            user_id=request.user_id,
            user_input=request.message,
            context_trigger=request.context
        )
        
        # Try to make audio if we can
        # If it fails, just return text (no worries)
        audio_b64 = None
        try:
            audio_bytes = voice_manager.generate_voice(ai_reply)
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as v_err:
            print(f"Voice broke: {v_err}") # It's fine, just print it
        
        return ChatResponse(response=ai_reply, audio_base64=audio_b64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
