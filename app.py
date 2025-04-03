from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import logging
import time
from openai import OpenAI
from dotenv import load_dotenv
from pyswip import Prolog

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ssense_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ssense_chatbot")

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:*", "file://*", "null"],
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"]
     }},
     supports_credentials=True)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

client = OpenAI()
logger.info("OpenAI client initialized")

# Load prompts
try:
    with open("nlu_prompt.txt") as f:
        nlu_prompt = f.read()
    with open("nlg_prompt.txt") as f:
        nlg_prompt = f.read()
    logger.info("Prompt files loaded successfully")
except Exception as e:
    logger.error(f"Error loading prompt files: {e}")
    raise

# Initialize Prolog
try:
    prolog = Prolog()
    logger.info("Prolog engine initialized")
    prolog.consult("ssense_policy.pl")
    logger.info("Prolog policy file loaded successfully")
except Exception as e:
    logger.error(f"Error initializing Prolog: {e}")
    raise

@app.route('/api/chat/welcome', methods=['GET'])
def welcome_message():
    origin = request.headers.get('Origin', '*')
    headers = {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }
    return jsonify({
        'message': 'Welcome to SSENSE support. How can I help you with your returns questions today?'
    }), 200, headers

@app.route('/api/chat', methods=['OPTIONS'])
def handle_options():
    logger.info("OPTIONS request received")
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/chat', methods=['POST'])
def process_message():
    start_time = time.time()
    origin = request.headers.get('Origin', '*')
    headers = {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }

    data = request.json
    user_question = data.get('message', '')
    if not user_question:
        return jsonify({'error': 'No message provided'}), 400, headers

    try:
        logger.info("Step 1: Running NLU")
        nlu_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": nlu_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.2
        )
        raw_nlu_output = nlu_response.choices[0].message.content.strip()

        if raw_nlu_output.startswith("```"):
            raw_nlu_output = raw_nlu_output.strip("`").strip()
            if raw_nlu_output.startswith("json"):
                raw_nlu_output = raw_nlu_output[4:].strip()

        nlu_json = json.loads(raw_nlu_output)
        facts = nlu_json["args"]["Facts"]
        logger.debug(f"Parsed Facts: {facts}")

        prolog_facts = "[" + ", ".join(facts) + "]"
        query = f"decide({prolog_facts}, Result)"
        logger.info(f"Running Prolog query: {query}")

        result = list(prolog.query(query, maxresult=1))
        result_value = result[0]['Result'] if result else None

        logger.info(f"Prolog result: {result_value}")

        logger.info("Step 3: Running NLG")
        kb_result = {
            "predicate": "decide",
            "args": {"Facts": facts},
            "result": result_value
        }

        nlg_input = {
            "user_question": user_question,
            "kb_result": kb_result
        }

        nlg_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": nlg_prompt},
                {"role": "user", "content": json.dumps(nlg_input, indent=2)}
            ],
            temperature=0.3
        )

        final_answer = nlg_response.choices[0].message.content

        return jsonify({
            'response': final_answer,
            'debug': {
                'nlu': nlu_json,
                'prolog_result': kb_result
            }
        }), 200, headers

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process message',
            'details': str(e)
        }), 500, headers

if __name__ == '__main__':
    logger.info("Starting SSENSE chatbot API on http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)