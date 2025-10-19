import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, FileResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from dotenv import load_dotenv
import requests, time
from io import BytesIO

# --- Import Customer Data ---
# Assuming your customer data is in 'utils/customer_data.py'
from api.utils.customer_data import customer_id_map, customer_security_map, customer_account_id_map

# Assuming your services are in an 'api/services' directory
from api.services.elevenlabs_service import elevenlabs_service
from api.services.gemini_service import gemini_service

load_dotenv()
os.makedirs("./audio", exist_ok=True)

app = FastAPI()

# --- Configuration ---
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
# IMPORTANT: Use 'https' for your public URL when working with Twilio
PUBLIC_BASE_URL = 'https://relaxatory-unsanguinely-delisa.ngrok-free.dev'
MAX_SECURITY_ATTEMPTS = 3 # Number of attempts for security questions

# --- Twilio Client and Validator Initialization ---
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio_validator = RequestValidator(TWILIO_AUTH_TOKEN)


curr_user_name = ""
curr_user_id = ""
curr_account_id = ""

"""
 audio_content = elevenlabs_service.text_to_speech(initial_greeting)
    audio_file_path = "./audio/greeting.mp3"
    with open(audio_file_path, "wb") as f:
        f.write(audio_content)
    
    response.play(f"{PUBLIC_BASE_URL}/audio/greeting.mp3")
"""
def speak_string(text: str, response: VoiceResponse) :
    audio_content = elevenlabs_service.text_to_speech(text)
    audio_file_path = "./audio/recording.mp3"
    with open(audio_file_path, "wb") as f:
        f.write(audio_content)
    
    response.play(f"{PUBLIC_BASE_URL}/audio/recording.mp3")

async def validate_twilio_request(request: Request) -> bool:
    """Validate that a request is genuinely from Twilio."""
    try:
        signature = request.headers.get('X-TWILIO-SIGNATURE', '')
        # The URL must match what Twilio sees, including query parameters if any.
        url = str(request.url)
        # For POST requests, Twilio requires the POST parameters in the validation.
        post_data = await request.form()
        return twilio_validator.validate(url, post_data, signature)
    except Exception:
        return False

@app.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle an incoming Twilio voice call and start the verification process."""
    # Twilio validation can be skipped on the initial inbound call if not needed,
    # but it's good practice for all webhooks. The validator might fail on the
    # very first inbound POST if the URL has no params and form is empty,
    # so we can be more lenient here or adjust validation logic.
    # For simplicity, let's assume it's a valid call to start.

    response = VoiceResponse()
    # Greet the user and ask for their first name to start verification.
    initial_greeting = "Welcome to Capital One. I'm Mr. Monopoly, your virtual banking assistant. To get started, may I have your first name?"
    # initial_greeting = "first name"
    
    # We will generate the audio for the greeting to have a consistent voice
    audio_content = elevenlabs_service.text_to_speech(initial_greeting)
    audio_file_path = "./audio/greeting.mp3"
    with open(audio_file_path, "wb") as f:
        f.write(audio_content)
    
    response.play(f"{PUBLIC_BASE_URL}/audio/greeting.mp3")
    
    # Start recording their name.
    response.record(
        action="/handle-name-recording",
        maxLength=10,
        playBeep=False,
        timeout=3
    )
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/handle-name-recording")
async def handle_name_recording(request: Request):
    """Handle the user's spoken name and ask a security question."""
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    form_data = await request.form()
    recording_url = form_data.get('RecordingUrl')
    response = VoiceResponse()

    if not recording_url:
        speak_string("I didn't hear a name. Please say your first name.", response)
        response.record(action="/handle-name-recording", maxLength=10, playBeep=False, timeout=3)
        return Response(content=str(response), media_type="application/xml")

    try:
        # Transcribe the user's name
        rec_response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        audio_file = BytesIO(rec_response.content)
        user_name = elevenlabs_service.speech_to_text(audio_file).strip().capitalize()
        print(f"Transcribed Name: '{user_name}'")
        print(f"Transcribed Name (Filtered): '{''.join(filter(str.isalpha, user_name))}'")
        ## print customer_id map for debugging
        print(f"Customer ID Map Keys: {list(customer_id_map.keys())}")
        user_name = ''.join(filter(str.isalpha, user_name)).lower()
        global curr_user_name, curr_account_id, curr_user_id
        curr_user_name = user_name
        curr_account_id = customer_account_id_map.get(user_name, "")
        curr_user_id = customer_id_map.get(user_name, "")
        if user_name in customer_id_map:
            # Customer found, ask the first security question
            security_questions = customer_security_map.get(user_name, {})
            print(f"Security Questions for {user_name}: {security_questions}")
            first_question = list(security_questions.keys())[0] if security_questions else None

            if first_question:
                print(f"Asking security question for {user_name}: {first_question}")
                speak_string(f"Hello {user_name}, I will now verify your identity with a security question.", response)
                speak_string(first_question, response)
                # Record their answer, passing the name in the action URL and starting at attempt 1
                response.record(action=f"/handle-security-answer/{user_name}/1", maxLength=15, playBeep=False, timeout=4)
            else:
                speak_string("I found your account, but there are no security questions set up. Please contact support.", response)
                response.hangup()
        else:
            print(f"Customer '{user_name}' not found.")
            speak_string("I'm sorry, I couldn't find a customer with that name. Goodbye.", response)
            response.hangup()

    except Exception as e:
        print(f"Error handling name recording: {e}")
        speak_string("I encountered an error. Please call back later.", response)
        response.hangup()

    return Response(content=str(response), media_type="application/xml")


@app.post("/handle-security-answer/{name}/{attempt}")
async def handle_security_answer(name: str, attempt: int, request: Request):
    """
    Handle the security question answer, check correctness, and provide retries.
    """
    if not validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    response = VoiceResponse()
    form_data = await request.form()
    recording_url = form_data.get('RecordingUrl')

    security_questions = customer_security_map.get(name, {})
    first_question = list(security_questions.keys())[0]

    if not recording_url:
        speak_string("I didn't hear an answer. Please try again.", response)
        speak_string(first_question, response)
        response.record(action=f"/handle-security-answer/{name}/{attempt}", maxLength=15, playBeep=False, timeout=4)
        return Response(content=str(response), media_type="application/xml")

    try:
        # Transcribe the user's answer
        rec_response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        audio_file = BytesIO(rec_response.content)
        ## filter user_answer to remove punctuation and keep only letters
        
        user_answer = elevenlabs_service.speech_to_text(audio_file).strip().lower()
        user_answer = ''.join(filter(str.isalpha, user_answer)).lower()

        # Get the correct answer for comparison
        correct_answer = security_questions.get(first_question, "").lower()
        print(f"Attempt {attempt}: User '{name}' Answered: '{user_answer}'. Correct: '{correct_answer}'")

        if user_answer == correct_answer:
            # If verification is successful:
            verified_prompt = f"Thank you for verifying your identity, {name}. How can I help you today?"

            speak_string(verified_prompt, response)
            # Now, direct to the main AI conversation handler
            response.record(action="/handle-recording", maxLength=30, playBeep=False, timeout=3)
        else:
            # If the answer is incorrect
            if attempt < MAX_SECURITY_ATTEMPTS:
                next_attempt = attempt + 1
                speak_string("That is not correct. Let's try again.", response)
                speak_string(first_question, response)
                response.record(action=f"/handle-security-answer/{name}/{next_attempt}", maxLength=15, playBeep=False, timeout=4)
            else:
                speak_string("I'm sorry, you have exceeded the maximum number of attempts.", response)
                response.hangup()

    except Exception as e:
        print(f"Error handling security answer: {e}")
        speak_string("I apologize, but I encountered an error. Please try again later. Goodbye.", response)
        response.hangup()

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
        speak_string(("I didn't hear anything. Could you please repeat that?"), response)
        response.record(action="/handle-recording", maxLength=30, playBeep=False, timeout=3)
        return Response(content=str(response), media_type="application/xml")

    try:
        # Download the recording from Twilio
        recording_response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        recording_response.raise_for_status()

        # --- Start AI Processing ---
        # 1. Convert user's speech to text
        audio_file = BytesIO(recording_response.content)
        user_text = elevenlabs_service.speech_to_text(audio_file)
        print(f"Transcribed text: '{user_text}'")
        
        # 2. Get a text response from the Gemini AI
        ai_response_text = gemini_service.run_conversation(user_text, curr_user_name, curr_user_id, curr_account_id)
        print(f"AI Response: '{ai_response_text}'")
        
        response = VoiceResponse()

        # --- Conversation Flow Logic ---
        # 3. Check if the AI has decided the conversation is over
        if "[HANGUP]" in ai_response_text:
            final_message = ai_response_text.replace("[HANGUP]", "").strip()
            print(f"Hanging up with final message: '{final_message}'")
            
            if final_message:
                audio_content = elevenlabs_service.text_to_speech(final_message)
                audio_file_path = "./audio/response.mp3"
                with open(audio_file_path, "wb") as f:
                    f.write(audio_content)
                response.play(f"{PUBLIC_BASE_URL}/audio/response.mp3")
            
            response.hangup()
        else:
            # 4. If the conversation should continue
            print("Continuing conversation...")
            
            audio_content = elevenlabs_service.text_to_speech(ai_response_text)
            audio_file_path = "./audio/response.mp3"
            with open(audio_file_path, "wb") as f:
                f.write(audio_content)
            
            response.play(f"{PUBLIC_BASE_URL}/audio/response.mp3")

            # time.sleep(3)
            speak_string("Is there anything else you would like assistance with?", response)
            # time.sleep(1)
            
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
        speak_string("I apologize, but I encountered an error. Please try again later. Goodbye.", response)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

@app.get("/health")
async def health_check():
    """Health check endpoint to ensure the server is running."""
    return {"status": "healthy"}

