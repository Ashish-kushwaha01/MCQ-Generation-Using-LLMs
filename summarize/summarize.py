import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

load_dotenv()

genai.configure(
    api_key=os.getenv("GOOGLE_API_KEY")
)

SUMMARIZE_PROMPT = """
You are an AI assistant that generates professional and concise summaries from content.
Produce a brief summary followed by key points.

Format the output clearly using markdown.
"""

def extract_transcript(video_url):
    """Extract transcript from YouTube video"""
    try:
        # Extract video ID using regex for robustness
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
        if not video_id_match:
            return "Error: Invalid YouTube URL"
        
        video_id = video_id_match.group(1)
        ytt_api = YouTubeTranscriptApi()

        transcript = ytt_api.fetch(
            video_id=video_id,
            languages=['hi','en']
        )

        text = " ".join([snippet.text for snippet in transcript])
        return text
    except Exception as e:
        return f"Error extracting transcript: {str(e)}"

def scrape_web_content(url):
    """Scrape text content from any website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading/trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Limit text length to avoid token limits
        return text[:10000]
    except Exception as e:
        return f"Error scraping website: {str(e)}"

def generate_summary(content, is_video=False):
    """Generate summary using Gemini LLM"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        content_type = "video transcript" if is_video else "website content"
        full_prompt = f"{SUMMARIZE_PROMPT}\n\nContent Type: {content_type}\n\nContent:\n{content}"
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"
