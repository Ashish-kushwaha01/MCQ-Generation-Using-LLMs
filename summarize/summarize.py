import os
from dotenv import load_dotenv
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi


load_dotenv()

genai.configure(
    api_key=os.getenv("GOOGLE_API_KEY")
)

PROMPT = """
You are an AI assistant that generates concise summaries
and key points from YouTube video transcripts.

Produce a brief summary followed by key points.
"""


# -----------------------------
# Extract Transcript
# -----------------------------

def extract_transcript(video_url):

    try:

        video_id = video_url.split("v=")[-1].split("&")[0]

        ytt_api = YouTubeTranscriptApi()

        transcript = ytt_api.fetch(
            video_id=video_id,
            languages=['hi','en']
        )

        text = " ".join(
            [snippet.text for snippet in transcript]
        )

        return text

    except Exception as e:

        return f"Error extracting transcript: {e}"


# -----------------------------
# Gemini Summary
# -----------------------------

def generate_summary(transcript):

    model = genai.GenerativeModel(
        "gemini-2.5-flash"
    )

    response = model.generate_content(
        PROMPT + "\n\n" + transcript
    )

    return response.text