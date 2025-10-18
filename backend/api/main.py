import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, FileResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from dotenv import load_dotenv
import requests

from api.services.elevenlabs_service import elevenlabs_service
from api.services.gemini_service import gemini_service

load_dotenv()
os.makedirs("./audio", exist_ok=True)

app = FastAPI()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PUBLIC_BASE_URL = 'relaxatory-unsanguinely-delisa.ngrok-free.dev'

# Twilio configuration
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
twilio_validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))

async def validate_twilio_request(request: Request) -> bool:
    """Validate that the request is coming from Twilio"""
    # Get the request URL and POST data
    url = str(request.url)
    post_data = await request.form()
    
    # Get the X-Twilio-Signature header
    signature = request.headers.get('X-TWILIO-SIGNATURE', '')
    
    return twilio_validator.validate(url, post_data, signature)

@app.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio voice calls"""
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    response = VoiceResponse()
    response.say("Welcome to Nessie Bank. How can I help you today?")
    
    # Start recording
    response.record(
        action="/handle-recording",
        maxLength="30",
        playBeep=False,
        timeout="3"
    )
    
    return Response(content=str(response), media_type="application/xml")

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    file_path = f"./audio/{filename}"
    return FileResponse(file_path, media_type="audio/mp3")

@app.post("/handle-recording")
async def handle_recording(request: Request):
    """Process the recording and respond to the user"""
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    form_data = await request.form()
    print("got form_data")
    recording_url = form_data.get('RecordingUrl')
    print("got recording url")
    
    if not recording_url:
        raise HTTPException(status_code=400, detail="No recording URL provided")

    try:
        # Download the recording
        recording_response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if not recording_response.ok:
            raise HTTPException(status_code=500, detail="Failed to download recording")

        # Convert speech to text
        from io import BytesIO
        audio_file = BytesIO(recording_response.content)
        user_text = elevenlabs_service.speech_to_text(audio_file)
        print("Transcribed text:", user_text)
        # Process with Gemini
        ai_response = gemini_service.run_conversation(user_text)
        print("AI Response:", ai_response)
        # Convert response back to speech
        audio_content = elevenlabs_service.text_to_speech(ai_response)
        print("Generated audio content of length:", len(audio_content))
        # Store the audio response temporarily
        # In practice, you'd want to use cloud storage

        
        # public_audio_url = f"{PUBLIC_BASE_URL}/audio/response.wav"
        # response.play(public_audio_url)
        
        # Writes audio to temporary file
        temp_file_path = "./audio/response.mp3"
        with open(temp_file_path, "wb") as f:
            bytes = f.write(audio_content)  
            print(f"Wrote {bytes} bytes to response.mp3")
            # Puts audio in grok GET endpoint
            # serve_audio("response.wav")
        
        response = VoiceResponse()
        response.play("https://relaxatory-unsanguinely-delisa.ngrok-free.dev/audio/response.mp3")
        print("Prepared Twilio response to play audio.")
        # Create a Twilio response that plays the audio
        # response = VoiceResponse()
        # response.play(temp_file_path)
        
        # Ask if they need anything else
        # response.say("Is there anything else I can help you with?")
        # response.record(
        #     action="/handle-recording",
        #     maxLength="30",
        #     playBeep=True,
        #     timeout="3"
        # )
        print("response: ", str(response))
        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        print(f"Error processing recording: {str(e)}")
        response = VoiceResponse()
        response.say("I apologize, but I encountered an error. Please try again.")
        return Response(content=str(response), media_type="application/xml")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
