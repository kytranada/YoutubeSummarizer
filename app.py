import os
import re
import logging
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple

from flask import Flask, render_template, request, flash, redirect, url_for
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

# --- Configuration ---

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- API and App Initialization ---

# Configure Gemini API
try:
    gemini_api_key = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=gemini_api_key)
except KeyError:
    logger.critical("FATAL ERROR: GEMINI_API_KEY environment variable is not set.")
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Initialize Flask app
app = Flask(__name__)
# // REFACTORED: Use a more secure default for the secret key, or better yet, enforce it.
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    logger.critical("FATAL ERROR: FLASK_SECRET_KEY environment variable is not set.")
    raise ValueError("A FLASK_SECRET_KEY is required for session management (flash messages).")

# --- Constants ---

# // REFACTORED: Initialize the model once globally for efficiency
try:
    GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash-latest') # Using 1.5 Flash for better performance/cost
except Exception as e:
    logger.critical(f"Could not initialize Gemini model: {e}")
    raise

MAX_TRANSCRIPT_LENGTH = 100_000  # Increased limit, as Gemini can handle more context
YOUTUBE_URL_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)

# --- Helper Functions ---

def extract_video_id(url: str) -> Optional[str]:
    """
    // REFACTORED: Use a robust regex to extract the YouTube video ID from various URL formats.
    """
    if not isinstance(url, str):
        return None
    match = YOUTUBE_URL_REGEX.match(url.strip())
    return match.group(1) if match else None

def get_transcript_text(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetches and formats the transcript for a given video ID.
    Returns a tuple of (transcript_text, error_message).
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([d['text'] for d in transcript_list])
        if not transcript_text.strip():
            return None, "The transcript for this video is empty."
        return transcript_text, None
    except NoTranscriptFound:
        return None, "No transcript could be found for this video. It might be disabled or not auto-generated."
    except TranscriptsDisabled:
        return None, "Transcripts are disabled for this video."
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching transcript for video_id '{video_id}': {e}")
        return None, "An unexpected error occurred while trying to retrieve the video transcript."

def generate_summary_with_gemini(transcript_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    // REFACTORED: Uses the globally initialized model and has more specific error handling.
    Generates a summary using the Gemini API.
    Returns a tuple of (summary_text, error_message).
    """
    if len(transcript_text) > MAX_TRANSCRIPT_LENGTH:
        logger.warning(f"Transcript is too long ({len(transcript_text)} chars), truncating.")
        transcript_text = transcript_text[:MAX_TRANSCRIPT_LENGTH]

    prompt = f"""You are an expert content analyst. Please analyze the following YouTube video transcript and provide a comprehensive summary.

**Transcript:**
---
{transcript_text}
---

**Your Task:**
Provide your analysis in a clean, well-structured Markdown format. Include the following sections:

📝 One-Paragraph Summary
A concise overview of the video's main purpose and conclusion.

🔑 Key Takeaways
- A bulleted list of the most important points, insights, or findings.
- Use 3 to 5 bullet points.

📚 Main Topics
A brief list of the primary subjects discussed in the video.

💡 Actionable Advice (if applicable)
If the video provides clear steps or recommendations for the viewer, list them here. If not, omit this section.

Please ensure the entire response is clear, easy to read, and captures the essence of the video's content."""

    try:
        response = GEMINI_MODEL.generate_content(prompt)
        
        # // REFACTORED: Check for content blocking due to safety settings
        if not response.parts:
            # Check the finish reason if available
            finish_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else "UNKNOWN"
            logger.warning(f"Gemini response was blocked. Reason: {finish_reason}")
            return None, f"The model's response was blocked due to safety filters (Reason: {finish_reason})."

        return response.text, None
        
    except google_exceptions.ResourceExhausted as e:
        logger.error(f"Gemini API quota exceeded: {e}")
        return None, "The API quota has been exceeded. Please try again later."
    except google_exceptions.PermissionDenied as e:
        logger.error(f"Gemini API authentication error: {e}")
        return None, "API authentication failed. Please check your API key configuration."
    except Exception as e:
        logger.error(f"An unexpected error occurred with the Gemini API: {e}")
        return None, f"An error occurred while generating the summary. Please try again."

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    url = request.form.get('youtube_url', '').strip()
    if not url:
        flash('Please enter a YouTube URL.', 'error')
        return redirect(url_for('index'))

    # // REFACTORED: Simplified and more robust validation
    video_id = extract_video_id(url)
    if not video_id:
        flash('Invalid YouTube URL. Please provide a valid link.', 'error')
        return redirect(url_for('index'))

    # // REFACTORED: Single, efficient flow for getting transcript and handling errors.
    transcript_text, error = get_transcript_text(video_id)
    if error:
        flash(error, 'error')
        return redirect(url_for('index'))

    # Generate summary
    summary, error = generate_summary_with_gemini(transcript_text)
    if error:
        flash(error, 'error')
        return redirect(url_for('index'))

    return render_template('summary.html', summary=summary, video_id=video_id)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message="Page Not Found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return render_template('error.html', error_code=500, error_message="An internal server error occurred."), 500

if __name__ == '__main__':
    # debug=False is safer for any kind of deployment, even local testing.
    # The Werkzeug debugger can allow for arbitrary code execution.
    app.run(debug=False, host='0.0.0.0', port=5001)