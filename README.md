# Wikipedia Chatbot

A Flask-based chatbot that answers questions with factual information from Wikipedia and optionally Google Custom Search.

## Credits

Created by **Shlok**

GitHub Repository: https://github.com/shloksathe18-dotcom/ai-chatbot

## Features

- Simple chat interface with user and bot messages
- Human-like responses for natural conversation
- Simple mathematical operations and calculations
- Wikipedia API integration for factual information
- Optional Google Custom Search API integration
- Caching for 10 minutes to reduce API calls
- Rate limiting (10 requests per minute per IP)
- Responsive design using Bootstrap

## Requirements

- Python 3.7+
- Flask
- Requests

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/shloksathe18-dotcom/ai-chatbot
   cd ai-chatbot
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Set the following environment variables:

- `PORT` - Port to run the application on (default: 5000)
- `GOOGLE_API_KEY` - Google Custom Search API key (optional)
- `GOOGLE_CX` - Google Custom Search Engine ID (optional)

On Windows:
```
set PORT=5000
set GOOGLE_API_KEY=your_api_key
set GOOGLE_CX=your_cx
```

On Unix/Linux/Mac:
```
export PORT=5000
export GOOGLE_API_KEY=your_api_key
export GOOGLE_CX=your_cx
```

## Usage

Run the application:
```
python app.py
```

Open your browser and navigate to `http://localhost:5000` (or your configured PORT).

## API Endpoints

- `GET /` - Serve the chat interface
- `POST /api/chat` - Accept user questions and return answers

Request format:
```json
{
  "message": "user question"
}
```

Response format:
```json
{
  "answer": "Short summary answer",
  "sources": [{"title": "...", "url": "..."}],
  "confidence": "high|medium|low"
}
```

## How it works

1. The user enters a question in the chat interface
2. The frontend sends the question to the backend via `/api/chat`
3. The backend first checks its cache for a recent response
4. If not cached, it queries Wikipedia's REST API
5. If Wikipedia has no results and Google API keys are configured, it queries Google Custom Search
6. The response is cached for 10 minutes
7. The answer is sent back to the frontend with sources and confidence level