import os
import json
import requests
import time
import random
import re
import math
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

# Load human-like responses from JSON file
with open('responses.json', 'r') as f:
    HUMAN_RESPONSES = json.load(f)

# Rate limit settings
RATE_LIMIT = 10  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds

# Safe math functions for evaluation
SAFE_MATH_FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'ceil': math.ceil,
    'floor': math.floor,
    'pi': math.pi,
    'e': math.e
}

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

def is_math_expression(query):
    """
    Check if the query looks like a math expression.
    Allows numbers, spaces, and operators (+, -, *, /, ^, %, (), ., and math functions).
    """
    # Remove spaces for easier checking
    query_no_spaces = query.replace(' ', '')
    
    # Check if it contains only allowed characters
    allowed_pattern = r'^[0-9+\-*/^%().sqrtlogpwmcnedfai,]+$'
    return bool(re.match(allowed_pattern, query_no_spaces))

def evaluate_math_expression(expression):
    """
    Safely evaluate a math expression using restricted globals.
    Returns the result or an error message.
    """
    try:
        # Replace ^ with ** for Python exponentiation
        expression = expression.replace('^', '**')
        
        # Create a safe environment with only allowed functions
        safe_dict = {
            "__builtins__": {},
            **SAFE_MATH_FUNCTIONS
        }
        
        # Evaluate the expression
        result = eval(expression, safe_dict)
        
        # Format the result
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 10)  # Round to avoid floating point precision issues
            
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Invalid math expression: {str(e)}"

def get_human_response(message):
    """
    Check if the message matches any predefined human-like responses.
    Returns a random response from the matching category or None if no match.
    
    Example:
    >>> get_human_response("hello")
    "Hello! I'm Askuno, your smart Wikipedia assistant. How can I help you today?"
    """
    message_lower = message.lower().strip()
    
    # Check greetings
    if message_lower in HUMAN_RESPONSES["greetings"]:
        return random.choice(HUMAN_RESPONSES["greetings"][message_lower])
    
    # Check identity questions
    if message_lower in HUMAN_RESPONSES["identity"]:
        return random.choice(HUMAN_RESPONSES["identity"][message_lower])
    
    # Check if message contains greeting keywords
    for greeting in HUMAN_RESPONSES["greetings"]:
        if greeting in message_lower:
            return random.choice(HUMAN_RESPONSES["greetings"][greeting])
    
    # Check if message contains identity keywords
    for identity in HUMAN_RESPONSES["identity"]:
        if identity in message_lower:
            return random.choice(HUMAN_RESPONSES["identity"][identity])
    
    return None

def search_wikipedia(query):
    # Use wikipedia lib to get info
    try:
        wikipedia.set_lang("en")
        
        # Get a more detailed summary with 5 sentences
        summary = wikipedia.summary(query, sentences=5)
        
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
    
    # First, check for human-like responses
    human_response = get_human_response(message)
    if human_response:
        return jsonify({
            "answer": human_response,
            "sources": [],
            "confidence": "high"
        })
    
    # Check if it's a math expression
    if is_math_expression(message):
        result = evaluate_math_expression(message)
        if not result.startswith("Error") and not result.startswith("Invalid"):
            return jsonify({
                "answer": f"The result of {message} is *{result}*.",
                "sources": [{
                    "title": "Math Calculation",
                    "url": None
                }],
                "confidence": "high"
            })
        else:
            return jsonify({
                "answer": result,
                "sources": [],
                "confidence": "low"
            })
    
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