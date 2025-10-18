import os
from typing import BinaryIO
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')

TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
STS_URL = "https://api.elevenlabs.io/v1/speech-to-text"

class ElevenLabsService:
    @staticmethod
    def speech_to_text(audio_file: BinaryIO) -> str:
        """Convert speech to text using ElevenLabs API"""
        if not ELEVENLABS_API_KEY:
            raise ValueError("ElevenLabs API key is not configured.")

        files = {
            'file': ('audio.wav', audio_file, 'audio/wav')
        }
        
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY
        }
        
        # The FIX is to add the model_id in the 'data' payload
        data = {
            "model_id": "scribe_v1" 
        }

        response = requests.post(
            STS_URL,
            headers=headers,
            files=files,
            data=data
        )

        if not response.ok:
            error_text = response.text
            print(f"ElevenLabs STS Error: {error_text}")
            raise Exception(f"ElevenLabs Speech-to-Text Error: {response.status_code} {error_text}")

        result = response.json()
        if not isinstance(result.get('text'), str):
            raise Exception('ElevenLabs STS Error: Invalid response format.')
        
        return result['text']

    @staticmethod
    def text_to_speech(text: str) -> bytes:
        """Convert text to speech using ElevenLabs API"""
        if not ELEVENLABS_API_KEY:
            raise ValueError("ElevenLabs API key is not configured.")

        headers = {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json'
        }

        data = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }

        response = requests.post(
            TTS_URL,
            headers=headers,
            json=data
        )

        if not response.ok:
            error_text = response.text
            raise Exception(f"ElevenLabs TTS Error: {response.status_code} {error_text}")

        return response.content

elevenlabs_service = ElevenLabsService()
