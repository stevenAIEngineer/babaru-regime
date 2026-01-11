# Author: Steven Lansangan
# Manages Text-to-Speech using ElevenLabs
import os
import logging
from elevenlabs import ElevenLabs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceManager")

# Initialize Client
# Requires ELEVENLABS_API_KEY in env
key = os.getenv("ELEVENLABS_API_KEY")
logger.info(f"Init VoiceManager. API Key present: {bool(key)}")

try:
    client = ElevenLabs(api_key=key)
except Exception as e:
    logger.warning(f"Voice client init failed: {e}")
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
