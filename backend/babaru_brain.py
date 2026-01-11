# Author: Steven Lansangan
# Main logic for connecting to Gemini
# It connects the memory, prompt builder, and Google API together

import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import local modules
from utils import memory_manager
from backend import prompt_builder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BabaruBrain")

# Load environment variables
load_dotenv()

# Initialize Gemini Client
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logger.warning("GOOGLE_API_KEY not found! Check your .env file.")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "gemini-3-pro-preview"

def get_response(user_id: str, user_input: str, context_trigger: str = "CONTEXT_GENERAL") -> str:
    # This is where the magic happens
    # 1. Get user data
    # 2. Make the prompt
    # 3. Call Google
    # 4. Save what happened
    
    # 1. Fetch Memory
    # Check if user exists, if not make a new one
    user_memory = memory_manager.get_user_memory(user_id)
    if not user_memory:
        # Fallback/Auto-create for testing if missing
        logger.info(f"User {user_id} memory not found. Creating default.")
        memory_manager.create_user(user_id, "Traveler")
        user_memory = memory_manager.get_user_memory(user_id)

    # 2. Build Prompt
    system_instruction = prompt_builder.build_system_prompt(context_trigger, user_memory)
    
    # 3. Call Gemini
    if not API_KEY:
        return "[SYSTEM ERROR] Google API Key is missing. Please set it in .env."

    try:
        # Construct chat history
        # Fetch full history from memory
        raw_history = user_memory.get('conversations', [])
        
        # Take last 10 messages (5 turns)
        recent_history = raw_history[-10:] if raw_history else []
        
        # Format for Gemini API (convert 'content' to 'parts')
        # The SDK expects contents=[{'role': 'user', 'parts': ['text']}, ...]
        formatted_contents = []
        for msg in recent_history:
            role = "user" if msg['role'] == "user" else "model"
            formatted_contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg['content'])]
            ))
            
        # Add current user input
        formatted_contents.append(types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        ))
        
        response = client.models.generate_content(
            model=MODEL_ID,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7, 
            ),
            contents=formatted_contents
        )
        
        ai_reply = response.text
        
        # 4. Save History (Async in production, sync here)
        memory_manager.update_conversation_history(user_id, {"role": "user", "content": user_input})
        memory_manager.update_conversation_history(user_id, {"role": "model", "content": ai_reply})
        
        # 5. Post-Processing (Mission Updates)
        # Rudimentary keyword check for now. 
        # Future: Use structured output or function calling to update DB.
        if "MISSION COMPLETE" in ai_reply.upper():
            # Trigger mission completion logic
            logger.info("Mission completion detected by AI trigger.")
            # memory_manager.update_missions(...) 
        
        return ai_reply

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return f"[SYSTEM ERROR] Babaru's brain fried: {e}"

if __name__ == "__main__":
    print("--- Babaru Terminal Interface (Ctrl+C to exit) ---")
    user_id = "terminal_user"
    
    # Simple interactive loop
    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            # Simulate basic context detection for testing
            trigger = "CONTEXT_GENERAL"
            if "stuck" in user_input.lower():
                trigger = "CONTEXT_USER_STUCK"
            elif "morning" in user_input.lower():
                trigger = "CONTEXT_MORNING"
                
            response = get_response(user_id, user_input, trigger)
            print(f"Babaru: {response}")
            
    except KeyboardInterrupt:
        print("\nBabaru: Leaving so soon? Typical.")
