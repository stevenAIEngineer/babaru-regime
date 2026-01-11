# Babaru Regime - Cloud Backend 🤡☁️

Welcome to the cloud brain for **Babaru**, the AI companion regime! This is the backend server that powers the snarky plushie app.

**Author:** Steven Lansangan  
**Role:** Software AI/ML Engineer 🚀

---

## What is this?
This is a FastAPI server that acts as the "brain" for Babaru. It handles:
1.  **AI Logic**: Uses Google Gemini (gemini-3-pro-preview) to generate Babaru's snarky personality.
2.  **Memory**: Stores user conversations and ranks in a local database so he remembers you.
3.  **Voice**: Connects to ElevenLabs IO to give Babaru a voice.

It's deployed on **Railway** and provides an API for the mobile app to talk to.

## Tech Stack
*   **Language**: Python 3.12 🐍
*   **Framework**: FastAPI (for the API) & Streamlit (for local testing)
*   **AI Model**: Google Gemini 3.0 Pro
*   **Voice**: ElevenLabs API
*   **Database**: SQLite (Simple & local)

## How to Run Locally

1.  **Clone the repo**
    ```bash
    git clone https://github.com/stevenAIEngineer/babaru-regime.git
    cd babaru-regime
    ```

2.  **Install requirements**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Environment**
    Create a `.env` file with your keys:
    ```
    GOOGLE_API_KEY=your_gemini_key
    ELEVENLABS_API_KEY=your_voice_key
    ELEVENLABS_VOICE_ID=your_voice_id
    ```

4.  **Run the API**
    ```bash
    python3 api.py
    # Server starts on http://localhost:8000
    ```

## API Endpoint
Send a POST request to talk to Babaru:
`POST /v1/chat`

Body:
```json
{
  "user_id": "user123",
  "message": "Hello Babaru!",
  "context": "CONTEXT_GENERAL"
}
```

Response:
```json
{
  "response": "Classic Babaru snark here...",
  "audio_base64": "<audio_data>"
}
```

---
*Built with ❤️ (and a bit of chaos) by Steven Lansangan.*
