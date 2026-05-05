import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_URL = "https://api.sarvam.ai/text-to-speech"

def generate_audio_from_text(text, language_code="en-IN", speaker="shubh", pace=1.0):
    """
    Generate audio from text using Sarvam AI REST API.
    Returns the binary audio data.
    """
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY not found in environment variables.")

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "target_language_code": language_code,
        "speaker": speaker,
        "model": "bulbul:v3",
        "pace": pace,
        "speech_sample_rate": 24000,
        "enable_preprocessing": True
    }

    print(f"Requesting TTS from Sarvam AI for language: {language_code}, speaker: {speaker}")
    response = requests.post(SARVAM_URL, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "audios" in data and len(data["audios"]) > 0:
            # The API returns a list of base64 strings
            audio_base64 = data["audios"][0]
            return base64.b64decode(audio_base64)
        else:
            raise Exception("No audio data received from Sarvam AI.")
    else:
        error_msg = response.text
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", error_msg)
        except:
            pass
        raise Exception(f"Sarvam AI API error: {error_msg}")

def generate_content_for_audio(topic, style, duration):
    """
    Generate content using Gemini (since it's already used in the project)
    to be converted into audio.
    """
    import google.generativeai as genai
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found.")
        
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    print(f"Generating script for topic: {topic}, style: {style}")
    prompt = f"""
    You are an expert content creator. Generate a script for a {style} about the topic: "{topic}".
    The script should be approximately {duration} minutes long when spoken.
    
    Style: {style}
    Topic: {topic}
    Estimated Duration: {duration} minutes
    
    Provide ONLY the script text, without any stage directions or meta-information.
    """
    
    response = model.generate_content(prompt)
    return response.text
