import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from dotenv import load_dotenv

from services.elevenlabs_service import elevenlabs_service
from services.gemini_service import gemini_service

load_dotenv()

app = FastAPI()

# Twilio configuration
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
twilio_validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))

def validate_twilio_request(request: Request) -> bool:
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
        playBeep=True,
        timeout="3"
    )
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/handle-recording")
async def handle_recording(request: Request):
    """Process the recording and respond to the user"""
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    form_data = await request.form()
    recording_url = form_data.get('RecordingUrl')
    
    if not recording_url:
        raise HTTPException(status_code=400, detail="No recording URL provided")

    try:
        # Download the recording
        recording_response = requests.get(recording_url)
        if not recording_response.ok:
            raise HTTPException(status_code=500, detail="Failed to download recording")

        # Convert speech to text
        user_text = elevenlabs_service.speech_to_text(recording_response.content)
        
        # Process with Gemini
        ai_response = gemini_service.run_conversation(user_text)
        
        # Convert response back to speech
        audio_content = elevenlabs_service.text_to_speech(ai_response)
        
        # Store the audio response temporarily
        # In practice, you'd want to use cloud storage
        temp_file_path = "/tmp/response.mp3"
        with open(temp_file_path, "wb") as f:
            f.write(audio_content)
            
        # Create a Twilio response that plays the audio
        response = VoiceResponse()
        response.play(temp_file_path)
        
        # Ask if they need anything else
        response.say("Is there anything else I can help you with?")
        response.record(
            action="/handle-recording",
            maxLength="30",
            playBeep=True,
            timeout="3"
        )
        
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
