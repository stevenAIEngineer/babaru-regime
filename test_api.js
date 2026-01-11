// Author: Steven Lansangan
// Simple script to test the backend API
const API_URL = "https://babaru-regime-production.up.railway.app/v1/chat";

async function speakToBabaru(userInput) {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: "mobile_app_user", // Replace with actual user ID
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
            console.log("[Audio Data Received] Length:", data.audio_base64.length);
        }
        return data.response;

    } catch (error) {
        console.error("Error talking to Babaru:", error);
        return "Connection Error: Babaru is offline.";
    }
}

// Execute the test
console.log("Running JS Verification against Live Endpoint...");
speakToBabaru("This is a final verification from JavaScript.");
