import { ELEVENLABS_VOICE_ID } from "../constants";

const ELEVENLABS_API_KEY = '49f402ac81377bdc8dd97cde77920db5e7962a120f0950c14e49ff79f619bc62';

const TTS_URL = `https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE_ID}`;
const STS_URL = `https://api.elevenlabs.io/v1/speech-to-text`; // Correct endpoint for Speech-to-Text

export const elevenLabsService = {
  speechToText: async (audioBlob: Blob): Promise<string> => {
    if (!ELEVENLABS_API_KEY) throw new Error("ElevenLabs API key is not configured.");

    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    // FIX: Changed model_id to 'scribe_v1' as 'eleven_multilingual_v2' is not valid for the STS endpoint.
    formData.append('model_id', 'scribe_v1'); 

    const response = await fetch(STS_URL, {
      method: 'POST',
      headers: {
        'xi-api-key': ELEVENLABS_API_KEY,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("ElevenLabs STS Error:", errorText);
      throw new Error(`ElevenLabs Speech-to-Text Error: ${response.status} ${errorText}`);
    }

    const result = await response.json();
    if (typeof result.text !== 'string') {
        throw new Error('ElevenLabs STS Error: Invalid response format.');
    }
    return result.text;
  },

  textToSpeech: async (text: string): Promise<Blob> => {
    if (!ELEVENLABS_API_KEY) throw new Error("ElevenLabs API key is not configured.");
    
    const response = await fetch(TTS_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_API_KEY,
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_multilingual_v2",
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        },
      }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`ElevenLabs TTS Error: ${response.status} ${errorText}`);
    }

    return response.blob();
  },
};