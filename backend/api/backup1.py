import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, FileResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from dotenv import load_dotenv
import requests
from io import BytesIO

# Assuming your services are in an 'api/services' directory
from api.services.elevenlabs_service import elevenlabs_service
from api.services.gemini_service import gemini_service
from api.utils.customer_data import customer_security_map, customer_id_map

load_dotenv()
os.makedirs("./audio", exist_ok=True)

app = FastAPI()

# --- Configuration ---
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
# IMPORTANT: Use 'https' for your public URL when working with Twilio
PUBLIC_BASE_URL = 'https://relaxatory-unsanguinely-delisa.ngrok-free.dev'

# --- Twilio Client and Validator Initialization ---
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio_validator = RequestValidator(TWILIO_AUTH_TOKEN)


async def validate_twilio_request(request: Request) -> bool:
    """Validate that a request is genuinely from Twilio."""
    try:
        signature = request.headers.get('X-TWILIO-SIGNATURE', '')
        url = str(request.url)
        post_data = await request.form()
        return twilio_validator.validate(url, post_data, signature)
    except Exception:
        return False

@app.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle an incoming Twilio voice call and start the conversation."""
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    response = VoiceResponse()
    # Greet the user and start listening for their first response.
    incoming_call_text = """
    Welcome to Capital One.
    I'm Nessie, your virtual banking assistant.
    May I have your first name to get started?
    I will ask you a few security questions to verify your identity.
    """
    
    response.say(incoming_call_text)
    
    # Start recording the user's response.
    response.record(
        action="/handle-recording",
        maxLength=30,  # Max length of recording in seconds
        playBeep=False,
        timeout=3  # Seconds of silence to consider the recording complete
    )
    
    return Response(content=str(response), media_type="application/xml")

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files stored locally."""
    file_path = f"./audio/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mp3")
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/handle-recording")
async def handle_recording(request: Request):
    """
    Process a user's recording, get a response from an AI,
    and continue the conversation or hang up.
    """
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    form_data = await request.form()
    recording_url = form_data.get('RecordingUrl')
    
    # If the user was silent, prompt them to speak again.
    if not recording_url:
        response = VoiceResponse()
        response.say("I didn't hear anything. Could you please repeat that?")
        response.record(action="/handle-recording", maxLength=30, playBeep=False, timeout=3)
        return Response(content=str(response), media_type="application/xml")

    try:
        # Download the recording from Twilio
        recording_response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        recording_response.raise_for_status()  # Raise an exception for bad status codes

        # --- Start AI Processing ---
        # 1. Convert user's speech to text
        audio_file = BytesIO(recording_response.content)
        user_text = elevenlabs_service.speech_to_text(audio_file)
        print(f"Transcribed text: '{user_text}'")
        
        # 2. Get a text response from the Gemini AI
        ai_response_text = gemini_service.run_conversation(user_text)
        print(f"AI Response: '{ai_response_text}'")
        
        response = VoiceResponse()
        
        # --- Conversation Flow Logic ---
        # 3. Check if the AI has decided the conversation is over
        if "[HANGUP]" in ai_response_text:
            # Clean the hangup command from the final message
            final_message = ai_response_text.replace("[HANGUP]", "").strip()
            print(f"Hanging up with final message: '{final_message}'")
            
            if final_message:
                # Convert the final message to speech and play it
                audio_content = elevenlabs_service.text_to_speech(final_message)
                audio_file_path = "./audio/response.mp3"
                with open(audio_file_path, "wb") as f:
                    f.write(audio_content)
                response.play(f"{PUBLIC_BASE_URL}/audio/response.mp3")
            
            # End the call
            response.hangup()
        else:
            # 4. If the conversation should continue, create the loop
            print("Continuing conversation...")
            
            # Convert the AI's response to speech
            audio_content = elevenlabs_service.text_to_speech(ai_response_text)
            
            # Save the audio file to be served publicly
            audio_file_path = "./audio/response.mp3"
            with open(audio_file_path, "wb") as f:
                f.write(audio_content)
            
            # Play the AI's audio response
            response.play(f"{PUBLIC_BASE_URL}/audio/response.mp3")
            
            # CRITICAL: Record the user's NEXT response to continue the loop
            response.record(
                action="/handle-recording",
                maxLength=30,
                playBeep=False,
                timeout=3
            )

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        print(f"Error processing recording: {e}")
        response = VoiceResponse()
        response.say("I apologize, but I encountered an error. Please try again later. Goodbye.")
        response.hangup()  # Hang up on error to prevent infinite loops
        return Response(content=str(response), media_type="application/xml")

@app.get("/health")
async def health_check():
    """Health check endpoint to ensure the server is running."""
    return {"status": "healthy"}
