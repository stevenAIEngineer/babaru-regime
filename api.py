# Author: Steven Lansangan
# Simple API wrapper
# This is what connects to the internet
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
import os
import re

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
        
        # JukeBox Logic: Check for [PLAY_SONG: xyz]
        song_match = re.search(r"\[PLAY_SONG: (.*?)\]", ai_reply)
        audio_b64 = None
        
        if song_match:
            try:
                song_name = song_match.group(1).strip().lower()
                clean_reply = ai_reply.replace(song_match.group(0), "").strip() # Remove tag for text display (optional, or keep it?)
                # Actually, user wants "You want me to sing? okay, [sing] then..."
                # Use split to get intro and outro
                parts = ai_reply.split(song_match.group(0))
                intro_text = parts[0].strip() if len(parts) > 0 else ""
                outro_text = parts[1].strip() if len(parts) > 1 else ""
                
                # Paths
                song_path = f"assets/songs/{song_name}.mp3"
                if not os.path.exists(song_path):
                    print(f"Song not found: {song_path}")
                    # Fallback to standard TTS of the full text
                    audio_bytes = voice_manager.generate_voice(ai_reply)
                else:
                    # Generate parts
                    intro_bytes = voice_manager.generate_voice(intro_text) if intro_text else None
                    outro_bytes = voice_manager.generate_voice(outro_text) if outro_text else None
                    
                    # Mix
                    audio_bytes = voice_manager.mix_audio_sandwich(intro_bytes, song_path, outro_bytes)

                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
            except Exception as e:
                print(f"Jukebox crashed: {e}")
                # Fallback
                try:
                    audio_bytes = voice_manager.generate_voice(ai_reply)
                    if audio_bytes:
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                except:
                    pass
        else:
            # Standard Voice
            try:
                audio_bytes = voice_manager.generate_voice(ai_reply)
                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            except Exception as v_err:
                print(f"Voice broke: {v_err}") # It's fine, just print it
        
        return ChatResponse(response=ai_reply, audio_base64=audio_b64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Direct TTS Endpoint ---
class SpeakRequest(BaseModel):
    text: str

class SpeakResponse(BaseModel):
    audio_base64: Optional[str] = None

@app.post("/v1/speak", response_model=SpeakResponse)
async def speak_endpoint(request: SpeakRequest):
    """
    Direct Text-to-Speech (No LLM)
    """
    try:
        # Just generate voice directly
        audio_bytes = voice_manager.generate_voice(request.text)
        audio_b64 = None
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
        return SpeakResponse(audio_base64=audio_b64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Serve Static Frontend ---
from fastapi.responses import FileResponse

@app.get("/tts")
async def serve_tts_ui():
    return FileResponse('simple_tts.html')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
