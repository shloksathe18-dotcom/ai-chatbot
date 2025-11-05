import os
import json
import requests
import time
from flask import Flask, render_template, request, jsonify
from functools import wraps
import hashlib
from collections import defaultdict
import wikipedia

# Hidden trademark for ownership verification
_TRADEMARK = "©Theshlok2025"

app = Flask(__name__)

# Cache for storing responses
cache = {}
# Track requests per IP for rate limiting
request_times = defaultdict(list)

# Config stuff
PORT = int(os.environ.get('PORT', 5000))
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GOOGLE_CX = os.environ.get('GOOGLE_CX')

# Rate limit settings
RATE_LIMIT = 10  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()
        
        # Clean up old timestamps
        request_times[ip] = [timestamp for timestamp in request_times[ip] 
                           if now - timestamp < RATE_LIMIT_WINDOW]
        
        # Check if we hit the limit
        if len(request_times[ip]) >= RATE_LIMIT:
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Track this request
        request_times[ip].append(now)
        return f(*args, **kwargs)
    
    return decorated_function

def cached_response(query, duration=600):
    # 10 min cache
    query_hash = hashlib.md5(query.lower().encode()).hexdigest()
    if query_hash in cache:
        response, timestamp = cache[query_hash]
        if time.time() - timestamp < duration:
            return response
    return None

def cache_response(query, response):
    # Save response to cache
    query_hash = hashlib.md5(query.lower().encode()).hexdigest()
    cache[query_hash] = (response, time.time())

def search_wikipedia(query):
    # Use wikipedia lib to get info
    try:
        wikipedia.set_lang("en")
        
        # Just get 2 sentences
        summary = wikipedia.summary(query, sentences=2)
        
        # Get page info
        page = wikipedia.page(query)
        
        # Log the result
        print(f"Wikipedia result for '{query}': {summary}")
        
        return {
            "answer": summary,
            "sources": [{
                "title": page.title,
                "url": page.url
            }],
            "confidence": "high"
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Multiple options found
        print(f"Ambiguous query '{query}': {e}")
        return {
            "answer": "Your query is ambiguous. Please be more specific.",
            "sources": [],
            "confidence": "low"
        }
    except wikipedia.exceptions.PageError as e:
        # No page found
        print(f"Page not found for '{query}': {e}")
        return {
            "answer": "Sorry, I couldn't find any results for your query.",
            "sources": [],
            "confidence": "low"
        }
    except Exception as e:
        # Something else broke
        print(f"Error searching Wikipedia for '{query}': {e}")
        return {
            "answer": "Something went wrong.",
            "sources": [],
            "confidence": "low"
        }

def search_google(query):
    # Fallback to Google if needed
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return None
    
    try:
        google_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CX,
            'q': query,
            'num': 3
        }
        response = requests.get(google_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if items:
                # Use first result
                first_item = items[0]
                return {
                    "answer": first_item.get("snippet", ""),
                    "sources": [{
                        "title": first_item.get("title", ""),
                        "url": first_item.get("link", "")
                    } for item in items[:3]],
                    "confidence": "medium"
                }
    except Exception as e:
        print(f"Google search error: {e}")
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
@rate_limit
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({
            "answer": "Please provide a question.",
            "sources": [],
            "confidence": "low"
        })
    
    # Check if we have it cached
    cached = cached_response(message)
    if cached:
        return jsonify(cached)
    
    # Try Wikipedia first
    result = search_wikipedia(message)
    
    # If no wiki result, try Google
    if not result:
        result = search_google(message)
    
    # Still nothing? Generic response
    if not result:
        result = {
            "answer": "Sorry, I couldn't find reliable information for that topic.",
            "sources": [],
            "confidence": "low"
        }
    
    # Save to cache
    cache_response(message, result)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)