# YouTube Transcript Summarizer

YouTube Transcript Summarizer is a Flask web application that summarizes YouTube video transcripts using the OpenAI API. Users can input a YouTube URL, and the app retrieves the video's transcript and generates a concise summary with key points and keywords.

## Photos

## Features

- Extracts transcripts from YouTube videos.
- Generates summaries using OpenAI's GPT-3.5-turbo model.
- Displays the summary, notes, and keywords in a simple web interface.

## Prerequisites

- Python 3.7 or later
- Flask
- youtube-transcript-api
- openai

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kytranada/YoutubeSummarizer.git
   cd YoutubeVideoSummarizer
   ```

2. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   Open the `.env` file in the root directory of the project and add your OpenAI API key

   ```plaintext
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. **Run the application:**

   ```bash
   python app.py
   ```

2. **Open your web browser and go to:**

   ```plaintext
   http://127.0.0.1:5000/
   ```

3. **Enter a YouTube URL and click "Summarize" to get the video's summary.**
