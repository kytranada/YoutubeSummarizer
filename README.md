# YouTube Transcript Summarizer

YouTube Transcript Summarizer is a Flask web application that summarizes YouTube video transcripts using Google's Gemini 2.5 Flash AI model. Users can input a YouTube URL, and the app retrieves the video's transcript and generates a comprehensive summary with key insights, topics, and definitions.

## Photos
[![Screen-Shot-2024-06-02-at-12-38-21-PM.png](https://i.postimg.cc/bwzLh34v/Screen-Shot-2024-06-02-at-12-38-21-PM.png)](https://postimg.cc/w7GD5cqK)

[![Screen-Shot-2024-06-02-at-1-16-06-PM.png](https://i.postimg.cc/Y9ptfcPH/Screen-Shot-2024-06-02-at-1-16-06-PM.png)](https://postimg.cc/bGBXp58C)

## Features

- Extracts transcripts from YouTube videos
- Generates comprehensive summaries using Google's Gemini 2.5 Flash model
- Provides structured output with key insights, topics, and definitions
- Modern, responsive web interface with copy and download functionality
- Robust error handling and validation
- Real-time processing with loading indicators

## Prerequisites

- Python 3.7 or later
- Flask
- youtube-transcript-api
- google-generativeai

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

   Create and open the `.env` file in the root directory of the project and add your Gemini API key:

   ```plaintext
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

   To get a Gemini API key:
   1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   2. Create a new API key
   3. Copy the key to your `.env` file

## Usage

1. **Run the application:**

   ```bash
   python app.py
   ```

2. **Open your web browser and go to:**

   ```plaintext
   http://127.0.0.1:5000/
   ```

3. **Enter a YouTube URL and click "Summarize" to get the video's comprehensive summary.**

## Summary Output Format

The application generates summaries in the following structured format:

- **Summary**: Concise overview of the video content
- **Key Insights**: Most important takeaways and findings
- **Main Topics Covered**: Primary themes and subjects discussed
- **Key Terms & Definitions**: Technical terms and concepts explained
- **Action Items**: Actionable advice or steps (if applicable)

## API Features

- **Gemini 2.5 Flash**: Latest AI model for superior summarization
- **Structured Output**: Consistent, well-organized summaries
- **Error Handling**: Comprehensive error management and user feedback
- **Rate Limiting**: Built-in protection against API abuse
- **Validation**: Robust input validation and sanitization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
