from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key securely
openai.api_key = os.getenv('OPENAI_API_KEY')
model_engine = "gpt-3.5-turbo"

# Initialize Flask app
app = Flask(__name__)

# Function for extracting video ID from youtube link 
def get_id(input):
    equalpos = input.find('=')
    startpos = equalpos + 1
    substring = input[startpos:startpos + 11]
    return substring

# ChatGPT function
def get_summary(input):
    response = openai.ChatCompletion.create (
        model = 'gpt-3.5-turbo',
        messages=[{"role": "system", "content": 
        """Your output should use the following template:
        - Summary
        - Notes
        - Keywords
        You have been tasked with creating a concise summary of a YouTube video using its transcription.
        Make a summary of the transcript.
        In addition extract the most important keywords and any complex words not known to the average reader aswell as any acronyms mentioned. 
        For each keyword and complex word, provide an explanation and definition based on its occurrence in the transcription.
        Please ensure that the summary, bullet points, and explanations fit within the 800-word limit, while still offering a comprehensive and clear understanding of the videos content""" },
        {"role" : "user", "content": input}]       
    )
    return response['choices'][0]['message']['content']

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission
@app.route('/summarize', methods=['POST'])
def summarize():
    url = request.form['youtube_url']
    video_id = get_id(url)
    
    # Retrieve transcript from YouTube video
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    
    # Collect text from transcript data
    transcript_text = "\n".join([entry["text"] for entry in transcript_data])
    
    # Get summary from OpenAI
    summary = get_summary(transcript_text)
    
    return render_template('summary.html', summary=summary)

if __name__ == '__main__':
    app.run(debug=True)