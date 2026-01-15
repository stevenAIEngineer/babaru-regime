// Author: Steven Lansangan
// Simple script to test the backend API
// Updated to test singing capability locally
const API_URL = "http://localhost:8000/v1/chat";

async function speakToBabaru(userInput) {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: "test_script_user",
                message: userInput,
                context: "CONTEXT_GENERAL"
            }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        console.log("Babaru says:", data.response);
        if (data.audio_base64) {
            console.log("🎶 [Jukebox Audio Received] Size: " + (data.audio_base64.length / 1024).toFixed(2) + " KB");
        } else {
            console.log("⚠️ No Audio (Check server logs, likely ffmpeg missing locally)");
        }
        return data.response;

    } catch (error) {
        console.error("Error talking to Babaru:", error);
        return "Connection Error: Babaru is offline.";
    }
}

// Execute the test
console.log("Testing Jukebox Logic...");
speakToBabaru("Sing the anthem");
