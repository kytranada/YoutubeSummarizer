from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import openai
import os
import re
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key securely
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai.api_key = openai_api_key
model_engine = "gpt-3.5-turbo"

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Constants
MAX_TRANSCRIPT_LENGTH = 50000  # characters
SUPPORTED_YOUTUBE_DOMAINS = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']

def validate_youtube_url(url):
    """Validate YouTube URL format and extract video ID"""
    if not url or not isinstance(url, str):
        return None, "Invalid URL format"
    
    url = url.strip()
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check if it's a supported YouTube domain
        if not any(supported in domain for supported in SUPPORTED_YOUTUBE_DOMAINS):
            return None, "URL must be from YouTube"
        
        video_id = None
        
        # Handle different YouTube URL formats
        if 'youtu.be' in domain:
            video_id = parsed_url.path[1:]  # Remove leading slash
        elif 'youtube.com' in domain:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]
        
        if not video_id or len(video_id) != 11:
            return None, "Invalid YouTube video ID"
        
        return video_id, None
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return None, "Invalid URL format"

def get_video_metadata(video_id):
    """Get basic video metadata for validation"""
    try:
        # This is a basic check - in production you might want to use youtube-dl or similar
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        return {
            'has_transcript': True,
            'transcript_length': len(transcript_data)
        }
    except NoTranscriptFound:
        return {'has_transcript': False, 'error': 'No transcript available'}
    except TranscriptsDisabled:
        return {'has_transcript': False, 'error': 'Transcripts disabled for this video'}
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        return {'has_transcript': False, 'error': 'Unable to access video'}

def get_summary(transcript_text):
    """Generate summary with error handling"""
    try:
        if not transcript_text or len(transcript_text.strip()) == 0:
            raise ValueError("Empty transcript")
        
        if len(transcript_text) > MAX_TRANSCRIPT_LENGTH:
            logger.warning(f"Transcript too long ({len(transcript_text)} chars), truncating")
            transcript_text = transcript_text[:MAX_TRANSCRIPT_LENGTH] + "..."
        
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    "role": "system", 
                    "content": """Your output should use the following template:
                    - Summary
                    - Notes
                    - Keywords
                    You have been tasked with creating a concise summary of a YouTube video using its transcription.
                    Make a summary of the transcript.
                    In addition extract the most important keywords and any complex words not known to the average reader aswell as any acronyms mentioned. 
                    For each keyword and complex word, provide an explanation and definition based on its occurrence in the transcription.
                    Please ensure that the summary, bullet points, and explanations fit within the 800-word limit, while still offering a comprehensive and clear understanding of the videos content"""
                },
                {"role": "user", "content": transcript_text}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response['choices'][0]['message']['content']
        
    except openai.error.AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise ValueError("API authentication failed. Please check your API key.")
    except openai.error.RateLimitError:
        logger.error("OpenAI rate limit exceeded")
        raise ValueError("Rate limit exceeded. Please try again later.")
    except openai.error.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise ValueError("API service temporarily unavailable. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error in summary generation: {e}")
        raise ValueError("An unexpected error occurred. Please try again.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        url = request.form.get('youtube_url', '').strip()
        
        if not url:
            flash('Please enter a YouTube URL', 'error')
            return redirect(url_for('index'))
        
        # Validate YouTube URL
        video_id, error = validate_youtube_url(url)
        if error:
            flash(f'Invalid URL: {error}', 'error')
            return redirect(url_for('index'))
        
        # Check video metadata
        metadata = get_video_metadata(video_id)
        if not metadata['has_transcript']:
            flash(f'Cannot summarize this video: {metadata.get("error", "No transcript available")}', 'error')
            return redirect(url_for('index'))
        
        # Retrieve transcript from YouTube video
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            flash('This video does not have available transcripts', 'error')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Transcript retrieval error: {e}")
            flash('Unable to retrieve video transcript. Please try again.', 'error')
            return redirect(url_for('index'))
        
        # Collect text from transcript data
        transcript_text = "\n".join([entry["text"] for entry in transcript_data])
        
        if not transcript_text.strip():
            flash('No transcript content found', 'error')
            return redirect(url_for('index'))
        
        # Get summary from OpenAI
        summary = get_summary(transcript_text)
        
        return render_template('summary.html', summary=summary, video_id=video_id)
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Unexpected error in summarize route: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True)