# Author: Steven Lansangan
# Manages Text-to-Speech using ElevenLabs
import os
import logging
from elevenlabs import ElevenLabs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceManager")

# Get the key
key = os.getenv("ELEVENLABS_API_KEY")

if key:
    print(" hl Voice System: Online and ready.")
else:
    # Print a loud warning so I see it in the logs
    print("!!! WARNING: ElevenLabs API Key is MISSING !!!")
    print("Please add ELEVENLABS_API_KEY to your environment variables.")

try:
    client = ElevenLabs(api_key=key)
except Exception as e:
    print(f"Voice client crashed: {e}")
    client = None

import re

def generate_voice(text: str, voice_id: str = None) -> bytes:
    """
    Converts text to speech and returns raw audio bytes (mp3).
    """

    if not client:
        logger.error("ElevenLabs client not initialized.")
        return None

    # User should provide a specific voice ID in .env, or we fallback
    target_voice = voice_id or os.getenv("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"
    
    if not target_voice:
        logger.error("No Voice ID provided (arg or env).")
        return None

    # Just in case the prompt fails, we strip asterisks here too
    clean_text = re.sub(r'\*.*?\*', '', text).strip()
    
    logger.info(f"Generating voice for cleaned text: {clean_text[:50]}...")
    
    if not clean_text:
        return None

    try:
        # Generate audio generator
        # Using text_to_speech.convert for v1+ SDK compatibility
        audio_generator = client.text_to_speech.convert(
            text=clean_text,
            voice_id=target_voice,
            model_id="eleven_monolingual_v1"
        )
        
        # Convert generator to full bytes
        audio_bytes = b"".join(audio_generator)
        return audio_bytes
        
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return None

# --- Audio Mixing (The Jukebox) ---
from pydub import AudioSegment
import io

def mix_audio_sandwich(intro_bytes: bytes, song_path: str, outro_bytes: bytes) -> bytes:
    """
    Combines: Intro (TTS) + Song (File) + Outro (TTS) -> One MP3
    """
    try:
        combined = AudioSegment.empty()
        
        # 1. Add Intro
        if intro_bytes:
            intro = AudioSegment.from_file(io.BytesIO(intro_bytes), format="mp3")
            combined += intro
            
        # 2. Add Song
        if song_path and os.path.exists(song_path):
            song = AudioSegment.from_file(song_path) # pydub auto-detects format
            combined += song
            
        # 3. Add Outro
        if outro_bytes:
            outro = AudioSegment.from_file(io.BytesIO(outro_bytes), format="mp3")
            combined += outro
            
        # Export
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Mixing failed: {e}")
        return None
