# Nessie Bank Voice Assistant Backend

This is the backend service for the Nessie Bank Voice Assistant, which handles phone calls through Twilio and processes banking requests using AI.

## Features

- Voice call handling with Twilio
- Speech-to-text and text-to-speech conversion using ElevenLabs
- Natural language processing using Google's Gemini AI
- Banking operations through the Nessie API
- FastAPI-based REST API

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
GOOGLE_API_KEY=your_key_here
NESSIE_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
```

4. Run the server:
```bash
uvicorn api.main:app --reload
```

## API Endpoints

- `POST /voice`: Handles incoming Twilio voice calls
- `POST /handle-recording`: Processes voice recordings and returns responses
- `GET /health`: Health check endpoint

## Architecture

The backend is organized into several services:

- `elevenlabs_service.py`: Handles speech-to-text and text-to-speech conversion
- `gemini_service.py`: Processes natural language using Google's Gemini AI
- `nessie_service.py`: Interfaces with the Nessie banking API
- `main.py`: FastAPI application with Twilio integration

## Security

- All API keys are stored in environment variables
- Twilio request validation is implemented
- Error handling and logging are in place

## Development

To run the development server with hot reload:
```bash
uvicorn api.main:app --reload --port 8000
```

## Testing

To test the Twilio integration locally:
1. Install ngrok: `npm install -g ngrok`
2. Run ngrok: `ngrok http 8000`
3. Update your Twilio phone number's voice webhook URL with the ngrok URL
