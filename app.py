from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import logging
import time
from openai import OpenAI
from dotenv import load_dotenv
from pyswip import Prolog, Atom, Variable, Functor # Import necessary types from pyswip

# --- Configuration ---
KB_FILENAME = 'ssense_policy.pl'
NLU_PROMPT_FILE = "nlu_prompt.txt" # Assumes new prompt is saved here
NLG_PROMPT_FILE = "nlg_prompt.txt"
LOG_FILE = "ssense_debug.log"
ALLOWED_PREDICATES = [ # Predicates the LLM is allowed to call
    'is_eligible', 'get_return_window', 'get_shipping_cost',
    'get_return_label_info', 'get_return_fee', 'is_item_excluded',
    'get_initiation_method', 'can_exchange', 'get_contact_email',
    'get_contact_chat_availability', 'get_phone_number',
    'get_damaged_item_action', 'get_warranty_provider', 'is_warranty_by_ssense'
]
# Define output variables expected for each predicate (mapping name to position)
# Note: This is simplified; complex cases might need more sophisticated handling
# We'll primarily focus on single output variables for now or boolean success/fail
PREDICATE_OUTPUT_VARS = {
    'get_return_window': {1: 'Days'},
    'get_shipping_cost': {2: 'CostType'},
    'get_return_label_info': {2: 'LabelInfo'},
    'get_return_fee': {2: 'Amount', 3: 'Currency'},
    'is_item_excluded': {2: 'ReasonStructure'},
    'get_initiation_method': {2: 'Method'}, # Can have multiple results
    'can_exchange': {1: 'Result'},
    'get_contact_email': {1: 'Email'},
    'get_contact_chat_availability': {1: 'Availability'},
    'get_phone_number': {2: 'Number', 3: 'Hours'},
    'get_damaged_item_action': {1: 'Action'},
    'get_warranty_provider': {1: 'Provider'},
    'is_warranty_by_ssense': {1: 'Result'},
    'is_eligible': {} # Success/fail determined by query result list being empty or not
}

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ssense_chatbot")

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app,
     resources={r"/api/*": {
         "origins": ["http://localhost:*", "file://*", "null"], # Allow local dev origins
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"]
     }},
     supports_credentials=True)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Initialize OpenAI Client
try:
    client = OpenAI()
    logger.info("OpenAI client initialized")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}", exc_info=True)
    raise

# Load prompts
try:
    with open(NLU_PROMPT_FILE) as f:
        nlu_prompt = f.read()
    with open(NLG_PROMPT_FILE) as f:
        nlg_prompt = f.read()
    logger.info("Prompt files loaded successfully")
except Exception as e:
    logger.error(f"Error loading prompt files from '{NLU_PROMPT_FILE}' or '{NLG_PROMPT_FILE}': {e}", exc_info=True)
    # Allow app to start but log error, handle missing prompts later? Or raise. Raising is safer.
    raise

# Initialize Prolog
try:
    prolog = Prolog()
    logger.info("Prolog engine initialized")
    # Ensure the cleaned KB file exists and consult it
    if not os.path.exists(KB_FILENAME):
         logger.error(f"Prolog KB file '{KB_FILENAME}' not found.")
         raise FileNotFoundError(f"Prolog KB file '{KB_FILENAME}' not found.")
    prolog.consult(KB_FILENAME)
    logger.info(f"Prolog policy file '{KB_FILENAME}' loaded successfully")
except Exception as e:
    logger.error(f"Error initializing Prolog or loading KB: {e}", exc_info=True)
    raise

# --- Helper Function to Construct Prolog Query ---

def format_prolog_arg(value):
    """Formats a Python value into a Prolog-compatible string representation."""
    if isinstance(value, str):
        # Check if it represents an atom (no quotes needed unless special chars or starts upper)
        # Simple check: alphanumeric + underscore, starting lower, not 'true'/'false'
        if value.replace('_', '').isalnum() and value and value[0].islower() and value not in ['true', 'false']:
             return value
        else:
             # Escape single quotes within the string
             escaped_value = value.replace("'", "''")
             return f"'{escaped_value}'" # Strings/atoms needing quotes
    elif isinstance(value, bool):
        return str(value).lower() # true / false
    elif isinstance(value, (int, float)):
        return str(value)
    elif value is None:
         return '_' # Represent None as Prolog anonymous variable
    # Add handling for lists if needed
    # elif isinstance(value, list):
    #     formatted_list = [format_prolog_arg(item) for item in value]
    #     return f"[{', '.join(formatted_list)}]"
    else:
        # Default fallback: use repr, might need adjustment
        logger.warning(f"Unsupported type for Prolog formatting: {type(value)}. Using repr().")
        # Escape single quotes in repr output if it contains them
        repr_value = repr(value)
        if "'" in repr_value:
             # Basic escaping for repr output, might not be fully robust
             escaped_repr = repr_value.replace("'", "''")
             return f"'{escaped_repr}'"
        return repr_value


def construct_prolog_query(predicate_name, args_dict):
    """
    Constructs a Prolog query string from a predicate name and named arguments.
    Returns the query string and a list of output variable names.
    """
    logger.debug(f"Constructing query for predicate: {predicate_name} with args: {args_dict}")
    if predicate_name not in ALLOWED_PREDICATES:
        raise ValueError(f"Predicate '{predicate_name}' is not allowed.")

    # Define the argument order for each predicate (INPUT args only)
    # This needs to be maintained carefully!
    input_arg_order_map = {
        'is_eligible': ['ItemType', 'Condition', 'Packaging', 'Tags', 'DaysSinceDelivery'],
        'get_return_window': [],
        'get_shipping_cost': ['Region'],
        'get_return_label_info': ['Region'],
        'get_return_fee': ['Region'],
        'is_item_excluded': ['ItemType'],
        'get_initiation_method': ['UserType'],
        'can_exchange': [],
        'get_contact_email': [],
        'get_contact_chat_availability': [],
        'get_phone_number': ['PhoneType'],
        'get_damaged_item_action': [],
        'get_warranty_provider': [],
        'is_warranty_by_ssense': [],
    }

    if predicate_name not in input_arg_order_map:
         raise ValueError(f"Argument order mapping not defined for predicate: {predicate_name}")

    positional_args_formatted = []
    input_arg_names = input_arg_order_map[predicate_name]

    # Populate positional args based on the defined order and the input dict
    for arg_name in input_arg_names:
        if arg_name not in args_dict:
            # This ideally shouldn't happen if NLU status is 'success' and validation is done
            logger.error(f"Missing required argument '{arg_name}' for predicate '{predicate_name}' in args: {args_dict}")
            raise ValueError(f"Internal Error: Missing required argument '{arg_name}' for predicate '{predicate_name}'.")
        formatted_arg = format_prolog_arg(args_dict[arg_name])
        positional_args_formatted.append(formatted_arg)

    # Determine total arity and add output variables
    output_vars_map = PREDICATE_OUTPUT_VARS.get(predicate_name, {})
    output_var_names = list(output_vars_map.values()) # Get the names for later extraction
    total_arity = len(input_arg_names)
    if output_vars_map:
        total_arity = max(len(input_arg_names), max(output_vars_map.keys()))

    # Ensure list is long enough and place output variables
    current_len = len(positional_args_formatted)
    # Pad with anonymous variables if needed between input args and output vars
    while current_len < total_arity:
        positional_args_formatted.append("_")
        current_len += 1

    for pos, var_name in output_vars_map.items():
        # Prolog positions are 1-based, list indices are 0-based
        idx = pos - 1
        if idx >= len(positional_args_formatted):
             logger.error(f"Output variable position {pos} out of calculated bounds {len(positional_args_formatted)} for {predicate_name}")
             # This indicates an issue with PREDICATE_OUTPUT_VARS or input_arg_order_map definition
             raise ValueError(f"Internal configuration error for predicate {predicate_name}")
        positional_args_formatted[idx] = var_name # Use variable name (e.g., "CostType")

    # Construct the final query string
    query_string = f"{predicate_name}({', '.join(positional_args_formatted)})."
    logger.debug(f"Constructed query string: {query_string}, Output vars: {output_var_names}")
    return query_string, output_var_names


# --- Flask Routes ---

@app.route('/api/chat/welcome', methods=['GET'])
def welcome_message():
    # Standard welcome message endpoint
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
    # Handles CORS preflight requests
    logger.info("OPTIONS request received")
    response = jsonify({'status': 'ok'})
    origin = request.headers.get('Origin', '*')
    response.headers.add('Access-Control-Allow-Origin', origin or '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/chat', methods=['POST'])
def process_message():
    # Main chat processing endpoint
    start_time = time.time()
    origin = request.headers.get('Origin', '*')
    # Prepare CORS headers for the actual response
    headers = {
        'Access-Control-Allow-Origin': origin or '*',
        'Access-Control-Allow-Credentials': 'true'
    }

    # --- Input Handling ---
    try:
        data = request.json
        if data is None:
             logger.warning("Received request with no JSON body.")
             return jsonify({'error': 'Request body must be JSON.'}), 400, headers
        user_question = data.get('message', '')
        # --- TODO: Implement History Handling ---
        # history = data.get('history', []) # Get history from request if using client-side approach
        # logger.debug(f"Received history: {history}")
        # --- End History Handling Placeholder ---

        if not user_question:
            logger.warning("Received request with no message.")
            return jsonify({'error': 'No message provided'}), 400, headers
        logger.info(f"Received user question: {user_question}")
    except Exception as req_err:
        logger.error(f"Error parsing request data: {req_err}", exc_info=True)
        return jsonify({'error': 'Invalid request format.'}), 400, headers


    try:
        # === Step 1: NLU/Planning using LLM ===
        logger.info("Step 1: Running NLU/Planning LLM call")

        # --- TODO: Construct messages_for_nlu including history ---
        messages_for_nlu = [{"role": "system", "content": nlu_prompt}]
        # messages_for_nlu.extend(history) # Add history if implementing
        messages_for_nlu.append({"role": "user", "content": user_question})
        # --- End History Construction Placeholder ---

        nlu_response = client.chat.completions.create(
            model="gpt-4o", # Or your chosen model
            messages=messages_for_nlu,
            temperature=0.1, # Lower temperature for more deterministic JSON output
            response_format={"type": "json_object"} # Request JSON output
        )
        raw_nlu_output = nlu_response.choices[0].message.content.strip()
        logger.debug(f"Raw NLU output: {raw_nlu_output}")

        # Parse the JSON output from NLU
        try:
            nlu_json = json.loads(raw_nlu_output)
            logger.debug(f"Parsed NLU JSON: {json.dumps(nlu_json, indent=2)}")
        except json.JSONDecodeError as json_e:
            logger.error(f"Failed to parse NLU JSON output: {json_e}\nRaw output was: {raw_nlu_output}", exc_info=True)
            # Ask user to rephrase or try again, as NLU failed
            return jsonify({
                'response': "I'm having trouble understanding that. Could you please rephrase your question?",
                'debug': {'error': 'NLU JSON Parsing Failed', 'raw_nlu': raw_nlu_output}
            }), 200, headers # Return 200 OK but with an error message for the user

        # === Step 2: Process NLU Result - Check Status ===
        nlu_status = nlu_json.get("status")
        predicate_name = nlu_json.get("predicate")
        args_dict = nlu_json.get("args", {})

        if nlu_status == "missing_info":
            clarification = nlu_json.get("clarification_question", "Could you please provide some more details?")
            missing = nlu_json.get("missing_args", [])
            logger.info(f"NLU status: missing_info. Missing args: {missing}. Sending clarification: {clarification}")
            # Return clarification question to the user
            # --- TODO: Include updated history in response if implementing history ---
            # response_data = {'response': clarification, 'debug': {'nlu': nlu_json}}
            # response_data['history'] = messages_for_nlu[1:] # Exclude system prompt
            # response_data['history'].append({'role': 'assistant', 'content': clarification})
            # return jsonify(response_data), 200, headers
            # --- End History Placeholder ---
            return jsonify({
                'response': clarification,
                'debug': {'nlu': nlu_json}
            }), 200, headers


        elif nlu_status == "success":
            logger.info(f"NLU status: success. Predicate: {predicate_name}. Args: {args_dict}")
            # === Step 3: Construct and Execute Prolog Query ===
            if not predicate_name:
                 logger.error("NLU status was 'success' but no predicate name was provided.")
                 raise ValueError("NLU Error: Missing predicate name in successful NLU response.")

            try:
                # Validate predicate first
                if predicate_name not in ALLOWED_PREDICATES:
                     logger.error(f"NLU returned disallowed predicate: {predicate_name}")
                     raise ValueError(f"Internal Error: Attempted to call disallowed predicate '{predicate_name}'.")
                # Construct the query
                query_string, output_var_names = construct_prolog_query(predicate_name, args_dict)
                logger.info(f"Constructed Prolog query: {query_string}")
            except ValueError as construction_err:
                 logger.error(f"Error constructing Prolog query: {construction_err}", exc_info=True)
                 # Return an error message to the user
                 return jsonify({'error': 'Internal error preparing KB query.'}), 500, headers


            # Execute the query
            try:
                prolog_results_list = list(prolog.query(query_string)) # Use list to get all results
                logger.debug(f"Raw Prolog results list: {prolog_results_list}")
            except Exception as prolog_err:
                 logger.error(f"Error executing Prolog query '{query_string}': {prolog_err}", exc_info=True)
                 return jsonify({'error': 'Internal error querying knowledge base.'}), 500, headers


            # Process Prolog results
            kb_result_data = {}
            # Check if the query itself failed in Prolog (e.g., syntax error caught by pyswip)
            # Note: prolog.query often returns empty list on failure, specific exceptions are less common
            if prolog_results_list is None: # Should not happen with list() but as safety check
                 kb_result_data["success"] = False
                 kb_result_data["solutions"] = None # Indicate error
                 kb_result_data["error"] = "Prolog query execution failed."
                 logger.error(f"Prolog query execution failed for: {query_string}")
            elif not prolog_results_list:
                # Query yielded no results (logical failure or boolean false)
                kb_result_data["success"] = False
                kb_result_data["solutions"] = []
                logger.info(f"Prolog query yielded no results (interpreted as False/Fail for predicate {predicate_name}).")
            else:
                # Query succeeded
                kb_result_data["success"] = True
                solutions = []
                # Check if the result is just [{}] which means success with no vars bound
                if prolog_results_list == [{}]:
                     logger.info(f"Prolog query succeeded with no variable bindings for predicate {predicate_name}.")
                     solutions.append({}) # Represent success explicitly
                else:
                     # Process solutions and extract output variables
                     for solution in prolog_results_list:
                          # Convert Prolog terms in solution to Python types where possible
                          py_solution = {k: v for k, v in solution.items()} # Basic conversion
                          solutions.append(py_solution)
                     logger.info(f"Prolog query succeeded. Solutions processed: {solutions}")
                kb_result_data["solutions"] = solutions


            # === Step 4: Prepare Input for NLG ===
            logger.info("Step 4: Preparing input for NLG LLM call")
            # Structure containing info for the NLG prompt
            nlg_input_context = {
                "user_question": user_question,
                "kb_query": {
                    "predicate_called": predicate_name,
                    "args_provided": args_dict, # Arguments provided by NLU
                    "query_string": query_string, # The actual query executed
                    "result": kb_result_data # Structured result: success + list of solutions
                }
                # --- TODO: Add history to NLG context if needed ---
                # "history": history
                # --- End History Placeholder ---
            }
            logger.debug(f"NLG Input Context: {json.dumps(nlg_input_context, indent=2, default=str)}") # Use default=str for non-serializable types like Prolog terms

            # === Step 5: NLG using LLM ===
            logger.info("Step 5: Running NLG LLM call")
            try:
                nlg_response = client.chat.completions.create(
                    model="gpt-4o", # Or your chosen model
                    messages=[
                        {"role": "system", "content": nlg_prompt},
                        # Send the structured context as user message content
                        {"role": "user", "content": json.dumps(nlg_input_context, indent=2, default=str)}
                    ],
                    temperature=0.3 # Slightly higher temp for more natural language
                )
                final_answer = nlg_response.choices[0].message.content.strip()
                logger.info(f"Generated final answer: {final_answer}")
            except Exception as nlg_err:
                 logger.error(f"Error during NLG LLM call: {nlg_err}", exc_info=True)
                 # Fallback response if NLG fails
                 final_answer = "I found the information based on the policy, but I'm having trouble phrasing the answer right now. Please try rephrasing your question."


            # === Step 6: Return Final Answer ===
            end_time = time.time()
            logger.info(f"Total processing time: {end_time - start_time:.2f} seconds")
            # --- TODO: Include updated history in response if implementing history ---
            # response_data = {'response': final_answer, 'debug': {...}}
            # response_data['history'] = messages_for_nlu[1:] # Exclude system prompt
            # response_data['history'].append({'role': 'assistant', 'content': final_answer})
            # return jsonify(response_data), 200, headers
            # --- End History Placeholder ---
            return jsonify({
                'response': final_answer,
                'debug': { # Include debug info
                    'nlu': nlu_json,
                    'prolog_query': query_string,
                    'prolog_result': kb_result_data
                }
            }), 200, headers

        else:
            # Handle unexpected NLU status
            logger.error(f"Received unexpected NLU status: {nlu_status}")
            raise ValueError(f"Received unexpected NLU status: {nlu_status}")

    except FileNotFoundError as fnf_err:
         logger.error(f"Configuration file not found: {fnf_err}", exc_info=True)
         return jsonify({'error': 'Server configuration error (missing files).'}), 500, headers
    except ValueError as val_err: # Catch specific validation errors
         logger.error(f"Data validation or processing error: {val_err}", exc_info=True)
         return jsonify({'error': f'Failed to process message: {val_err}'}), 500, headers
    except Exception as e:
        # Catch-all for any other errors during processing
        logger.error(f"Unhandled error processing message: {str(e)}", exc_info=True)
        # Return a generic error response
        return jsonify({
            'error': 'Failed to process message due to an unexpected internal error.'
            # Avoid sending detailed exception 'e' to client in production
        }), 500, headers

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting SSENSE chatbot API on http://localhost:{port}")
    # Use waitress or gunicorn for production instead of Flask's debug server
    app.run(debug=False, host='0.0.0.0', port=port) # Set debug=False for production/testing

