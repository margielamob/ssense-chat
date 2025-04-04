# Filename: app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import logging
import time
from openai import OpenAI
from dotenv import load_dotenv
from pyswip import Prolog, Atom, Variable, Functor 

KB_FILENAME = 'ssense_policy.pl'
NLU_PROMPT_FILE = "nlu_prompt.txt" 
NLG_PROMPT_FILE = "nlg_prompt.txt"
LOG_FILE = "ssense_debug.log"
ALLOWED_PREDICATES = [ 
    'is_eligible', 'get_return_window', 'get_shipping_cost',
    'get_return_label_info', 'get_return_fee', 'is_item_excluded',
    'get_initiation_method', 'can_exchange', 'get_contact_email',
    'get_contact_chat_availability', 'get_phone_number',
    'get_damaged_item_action', 'get_warranty_provider', 'is_warranty_by_ssense'
]

PREDICATE_OUTPUT_VARS = {
    'get_return_window': {1: 'Days'},
    'get_shipping_cost': {2: 'CostType'},
    'get_return_label_info': {2: 'LabelInfo'},
    'get_return_fee': {2: 'Amount', 3: 'Currency'},
    'is_item_excluded': {2: 'ReasonStructure'},
    'get_initiation_method': {2: 'Method'}, 
    'can_exchange': {1: 'Result'},
    'get_contact_email': {1: 'Email'},
    'get_contact_chat_availability': {1: 'Availability'},
    'get_phone_number': {2: 'Number', 3: 'Hours'},
    'get_damaged_item_action': {1: 'Action'},
    'get_warranty_provider': {1: 'Provider'},
    'is_warranty_by_ssense': {1: 'Result'},
    'is_eligible': {} 
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ssense_chatbot")

app = Flask(__name__)

CORS(app,
     resources={r"/api/*": {
         "origins": ["http://localhost:*", "file://*", "null"], 
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"]
     }},
     supports_credentials=True)

load_dotenv()
logger.info("Environment variables loaded")

try:
    client = OpenAI()
    logger.info("OpenAI client initialized")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}", exc_info=True)
    raise

try:
    with open(NLU_PROMPT_FILE) as f:
        nlu_prompt = f.read()
    with open(NLG_PROMPT_FILE) as f:
        nlg_prompt = f.read()
    logger.info("Prompt files loaded successfully")
except Exception as e:
    logger.error(f"Error loading prompt files from '{NLU_PROMPT_FILE}' or '{NLG_PROMPT_FILE}': {e}", exc_info=True)
    
    raise

try:
    prolog = Prolog()
    logger.info("Prolog engine initialized")
    
    if not os.path.exists(KB_FILENAME):
        logger.error(f"Prolog KB file '{KB_FILENAME}' not found.")
        raise FileNotFoundError(f"Prolog KB file '{KB_FILENAME}' not found.")
    prolog.consult(KB_FILENAME)
    logger.info(f"Prolog policy file '{KB_FILENAME}' loaded successfully")
except Exception as e:
    logger.error(f"Error initializing Prolog or loading KB: {e}", exc_info=True)
    raise


def format_prolog_arg(value):
    """Formats a Python value into a Prolog-compatible string representation."""
    if isinstance(value, str):
        if value.replace('_', '').isalnum() and value and value[0].islower() and value not in ['true', 'false']:
              return value
        else:
              escaped_value = value.replace("'", "''")
              return f"'{escaped_value}'" 
    elif isinstance(value, bool):
        return str(value).lower() 
    elif isinstance(value, (int, float)):
        return str(value)
    elif value is None:
         return '_' 
    else:
        logger.warning(f"Unsupported type for Prolog formatting: {type(value)}. Using repr().")
        repr_value = repr(value)
        if "'" in repr_value:
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
    
    for arg_name in input_arg_names:
        if arg_name not in args_dict:
            logger.error(f"Missing required argument '{arg_name}' for predicate '{predicate_name}' in args: {args_dict}")
            raise ValueError(f"Internal Error: Missing required argument '{arg_name}' for predicate '{predicate_name}'.")
        formatted_arg = format_prolog_arg(args_dict[arg_name])
        positional_args_formatted.append(formatted_arg)
    
    output_vars_map = PREDICATE_OUTPUT_VARS.get(predicate_name, {})
    output_var_names = list(output_vars_map.values()) 
    total_arity = len(input_arg_names)
    if output_vars_map:
        max_output_pos = max(output_vars_map.keys()) if output_vars_map else 0
        total_arity = max(len(input_arg_names), max_output_pos)

    current_len = len(positional_args_formatted)
    
    while current_len < total_arity:
        positional_args_formatted.append("_")
        current_len += 1

    for pos, var_name in output_vars_map.items():
        idx = pos - 1
        if idx >= len(positional_args_formatted):
             logger.error(f"Output variable position {pos} out of calculated bounds {len(positional_args_formatted)} for {predicate_name}")
             raise ValueError(f"Internal configuration error for predicate {predicate_name}: PREDICATE_OUTPUT_VARS position mismatch.")
        positional_args_formatted[idx] = var_name 

    query_string = f"{predicate_name}({', '.join(positional_args_formatted)})."
    logger.debug(f"Constructed query string: {query_string}, Output vars: {output_var_names}")
    return query_string, output_var_names


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
    origin = request.headers.get('Origin', '*')
    response.headers.add('Access-Control-Allow-Origin', origin or '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/chat', methods=['POST'])
def process_message():
    start_time = time.time()
    origin = request.headers.get('Origin', '*')
    headers = {
        'Access-Control-Allow-Origin': origin or '*',
        'Access-Control-Allow-Credentials': 'true'
    }

    try:
        data = request.json
        if data is None:
             logger.warning("Received request with no JSON body.")
             return jsonify({'error': 'Request body must be JSON.'}), 400, headers
        user_question = data.get('message', '')
        if not user_question:
            logger.warning("Received request with no message.")
            return jsonify({'error': 'No message provided'}), 400, headers
        logger.info(f"Received user question: {user_question}")
    except Exception as req_err:
        logger.error(f"Error parsing request data: {req_err}", exc_info=True)
        return jsonify({'error': 'Invalid request format.'}), 400, headers

    try:
        logger.info("Step 1: Running NLU/Planning LLM call")
        messages_for_nlu = [{"role": "system", "content": nlu_prompt}]
        messages_for_nlu.append({"role": "user", "content": user_question})

        nlu_response = client.chat.completions.create(
            model="gpt-4o", 
            messages=messages_for_nlu,
            temperature=0.1, 
            response_format={"type": "json_object"} 
        )
        raw_nlu_output = nlu_response.choices[0].message.content.strip()
        logger.debug(f"Raw NLU output: {raw_nlu_output}")

        try:
            nlu_json = json.loads(raw_nlu_output)
            logger.debug(f"Parsed NLU JSON: {json.dumps(nlu_json, indent=2)}")
        except json.JSONDecodeError as json_e:
            logger.error(f"Failed to parse NLU JSON output: {json_e}\nRaw output was: {raw_nlu_output}", exc_info=True)
            return jsonify({
                'response': "I'm having trouble understanding that. Could you please rephrase your question?",
                'debug': {'error': 'NLU JSON Parsing Failed', 'raw_nlu': raw_nlu_output}
            }), 200, headers 

        nlu_status = nlu_json.get("status")
        predicate_name = nlu_json.get("predicate")
        args_dict = nlu_json.get("args", {})

        if nlu_status == "missing_info":
            clarification = nlu_json.get("clarification_question", "Could you please provide some more details?")
            missing = nlu_json.get("missing_args", [])
            logger.info(f"NLU status: missing_info. Missing args: {missing}. Sending clarification: {clarification}")
            return jsonify({
                'response': clarification,
                'debug': {'nlu': nlu_json}
            }), 200, headers

        elif nlu_status == "off_topic": 
            reason = nlu_json.get("off_topic_reason", "The question doesn't seem related to our return policy.")
            logger.info(f"NLU status: off_topic. Reason: {reason}. Generating canned response.")
            final_answer = "I can only help with questions about the SSENSE return policy. Could you ask something related to returns, please?"
            return jsonify({
                'response': final_answer,
                'debug': {'nlu': nlu_json}
            }), 200, headers

        elif nlu_status == "success":
            logger.info(f"NLU status: success. Predicate: {predicate_name}. Args: {args_dict}")
            if not predicate_name:
                 logger.error("NLU status was 'success' but no predicate name was provided.")
                 raise ValueError("NLU Error: Missing predicate name in successful NLU response.")

            try:
                if predicate_name not in ALLOWED_PREDICATES:
                      logger.error(f"NLU returned disallowed predicate: {predicate_name}")
                      raise ValueError(f"Internal Error: Attempted to call disallowed predicate '{predicate_name}'.")
                query_string, output_var_names = construct_prolog_query(predicate_name, args_dict)
                logger.info(f"Constructed Prolog query: {query_string}")
            except ValueError as construction_err:
                 logger.error(f"Error constructing Prolog query: {construction_err}", exc_info=True)
                 return jsonify({'error': 'Internal error preparing KB query.'}), 500, headers

            try:
                prolog_results_list = list(prolog.query(query_string)) 
                logger.debug(f"Raw Prolog results list: {prolog_results_list}")
            except Exception as prolog_err:
                 logger.error(f"Error executing Prolog query '{query_string}': {prolog_err}", exc_info=True)
                 return jsonify({'error': 'Internal error querying knowledge base.'}), 500, headers

            kb_result_data = {}
            if prolog_results_list is None: 
                 kb_result_data["success"] = False
                 kb_result_data["solutions"] = None 
                 kb_result_data["error"] = "Prolog query execution failed."
                 logger.error(f"Prolog query execution failed for: {query_string}")
            elif not prolog_results_list:
                kb_result_data["success"] = False
                kb_result_data["solutions"] = []
                logger.info(f"Prolog query yielded no results (interpreted as False/Fail for predicate {predicate_name}).")
            else:
                kb_result_data["success"] = True
                solutions = []
                if prolog_results_list == [{}]:
                      logger.info(f"Prolog query succeeded with no variable bindings for predicate {predicate_name}.")
                      solutions.append({}) 
                else:
                      for solution in prolog_results_list:
                            py_solution = {}
                            for k, v in solution.items():
                                if isinstance(v, Atom):
                                    py_solution[k] = str(v).strip("'")
                                elif isinstance(v, Functor) and v.arity == 0:
                                    py_solution[k] = str(v).strip("'") 
                                else:
                                    py_solution[k] = v
                            solutions.append(py_solution)
                      logger.info(f"Prolog query succeeded. Solutions processed: {solutions}")
                kb_result_data["solutions"] = solutions

            explanation_string = None
            if kb_result_data.get("success"):
                try:
                    exp_query = f"predicate_explanation({predicate_name}, _, Explanation)."
                    explanation_results = list(prolog.query(exp_query))
                    if explanation_results:
                        explanation_raw = explanation_results[0].get('Explanation', None)
                        if explanation_raw is not None:
                             explanation_string = str(explanation_raw).strip("'") 
                        logger.info(f"Retrieved explanation for {predicate_name}: {explanation_string}")
                    else:
                        logger.info(f"No explanation found for predicate: {predicate_name}")
                except Exception as exp_err:
                    logger.error(f"Error querying explanation for {predicate_name}: {exp_err}", exc_info=True)

            logger.info("Step 4: Preparing input for NLG LLM call")
            nlg_input_context = {
                "user_question": user_question,
                "kb_query": {
                    "predicate_called": predicate_name,
                    "args_provided": args_dict, 
                    "query_string": query_string, 
                    "result": kb_result_data 
                }
            }
            logger.debug(f"NLG Input Context: {json.dumps(nlg_input_context, indent=2, default=str)}") 

            logger.info("Step 5: Running NLG LLM call")
            try:
                nlg_response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {"role": "system", "content": nlg_prompt},
                        {"role": "user", "content": json.dumps(nlg_input_context, indent=2, default=str)}
                    ],
                    temperature=0.3 
                )
                final_answer = nlg_response.choices[0].message.content.strip()
                logger.info(f"Generated final answer: {final_answer}")
            except Exception as nlg_err:
                 logger.error(f"Error during NLG LLM call: {nlg_err}", exc_info=True)
                 final_answer = "I found the information based on the policy, but I'm having trouble phrasing the answer right now. Please try rephrasing your question."

            end_time = time.time()
            logger.info(f"Total processing time: {end_time - start_time:.2f} seconds")
            
            response_data = {
                'response': final_answer,
                'explanation': explanation_string,
                'debug': { 
                    'nlu': nlu_json,
                    'prolog_query': query_string,
                    'prolog_result': kb_result_data 
                }
            }
            return jsonify(response_data), 200, headers

        else:
            logger.error(f"Received unexpected NLU status: {nlu_status}. NLU JSON: {nlu_json}")
            return jsonify({
                'response': "I'm sorry, I encountered an unexpected issue understanding that request.",
                 'debug': {'nlu': nlu_json}
            }), 200, headers 

    except FileNotFoundError as fnf_err:
        logger.error(f"Configuration file not found: {fnf_err}", exc_info=True)
        return jsonify({'error': 'Server configuration error (missing files).'}), 500, headers
    except ValueError as val_err: 
        logger.error(f"Data validation or processing error: {val_err}", exc_info=True)
        return jsonify({'error': f'Failed to process message: {val_err}'}), 500, headers 
    except Exception as e:
        logger.error(f"Unhandled error processing message: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process message due to an unexpected internal error.'
        }), 500, headers

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting SSENSE chatbot API on http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)
