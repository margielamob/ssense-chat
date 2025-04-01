import cohere
import json
import time
import os
from dotenv import load_dotenv

# Import specific errors available in cohere==5.14.0
from cohere.errors import (
    TooManyRequestsError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    InternalServerError,
    ServiceUnavailableError
)

# --- Configuration ---
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
INPUT_FILENAME = "cleaned_sentences.json"
OUTPUT_FILENAME = "cohere_extracted_rules_v4.json" # Increment output filename
COHERE_MODEL = "command-a-03-2025"
REQUESTS_PER_MINUTE_LIMIT = 10
SLEEP_TIME_SECONDS = 61

# --- Cohere Client Initialization ---
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY environment variable not set.")
print(f"Initializing Cohere client for model: {COHERE_MODEL}")
co = cohere.Client(COHERE_API_KEY, client_name="logic_extractor_script", timeout=120)

# --- Load Input Data ---
try:
    with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
        cleaned_sentences = json.load(f)
    if not isinstance(cleaned_sentences, list):
        raise TypeError(f"{INPUT_FILENAME} should contain a JSON list of strings.")
    print(f"Loaded {len(cleaned_sentences)} sentences from {INPUT_FILENAME}")
except FileNotFoundError:
    print(f"Error: Input file '{INPUT_FILENAME}' not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{INPUT_FILENAME}'.")
    exit(1)
except Exception as e:
    print(f"Error loading input file: {e}")
    exit(1)


# --- Define the JSON Schema for the response format ---
response_format = {
  "type": "json_object",
  "json_schema": {
    "type": "object",
    "title": "Return Policy Logic",
    "description": "Structured representation of return policy rules.",
    "properties": {
      "rules": {
        "type": "array",
        "description": "A list of symbolic rules extracted from the sentence.",
        "items": {
          "type": "object",
          "properties": {
            "rule": {
                "type": "string",
                "description": "The symbolic rule identifier (e.g., returnWindow, itemCondition)."
             },
            "conditions": {
                "type": "object",
                "description": "An object containing the specific conditions for the rule. Structure depends on the rule.",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "The type of condition (e.g., 'time', 'state', 'requirement')"
                    }
                },
                "required": ["type"],
                "additionalProperties": True
            }
          },
          "required": ["rule", "conditions"]
        }
      }
    },
    "required": ["rules"]
  }
}


def make_prompt(sentence):
    # Prompt instructing the model to extract rules into the specified JSON format
    return f"""Analyze the following return policy sentence and extract the core logic into a structured JSON format.
Strictly adhere to the required JSON schema: the output MUST be a JSON object containing a single key "rules", which is an array of rule objects. Each rule object MUST have a "rule" (string identifier) and "conditions" (object detailing the rule specifics). The conditions object MUST have at least a "type" field and can contain additional key-value pairs. Do not include explanations, markdown formatting, or any text outside the final JSON object.

Schema Reminder:
{{
  "rules": [
    {{
      "rule": "string",
      "conditions": {{
        "type": "string", // Required field, describes the condition type
        // Can contain additional key-value pairs
      }}
    }}
    // , ... more rule objects if applicable
  ]
}}

Symbolic Rule Examples (Use these or create analogous ones):
- Rule: "returnWindow", Conditions: {{type: "time", days: 30, basis: "delivery"}}
- Rule: "itemCondition", Conditions: {{type: "state", required: ["unworn", "tags_attached", "original_packaging"]}}
- Rule: "eligibility", Conditions: {{type: "requirement", reason: "defective", condition: "unused"}}
- Rule: "finalSale", Conditions: {{type: "restriction", category: "clearance"}}
- Rule: "requires", Conditions: {{type: "documentation", document: "proof_of_purchase"}}
- Rule: "refund", Conditions: {{type: "payment", method: "original_payment", condition: "quality_check_passed"}}

Sentence to Analyze:
"{sentence}"

JSON Output:
"""

# --- Process Sentences ---
extracted_logic = []
request_count = 0
total_sentences = len(cleaned_sentences)

for i, sentence in enumerate(cleaned_sentences):
    # --- Rate Limiting ---
    if request_count > 0 and request_count % REQUESTS_PER_MINUTE_LIMIT == 0:
        print(f"\n⏳ Rate limit threshold ({REQUESTS_PER_MINUTE_LIMIT} requests) reached. Sleeping for {SLEEP_TIME_SECONDS} seconds...")
        time.sleep(SLEEP_TIME_SECONDS)
        print("Resuming...")

    prompt = make_prompt(sentence)

    try:
        print(f"\n[{i+1}/{total_sentences}] Processing sentence: \"{sentence}\"")
        response = co.chat(
            message=prompt,
            model=COHERE_MODEL,
            temperature=0.1,
            response_format=response_format
        )
        request_count += 1

        output = response.text.strip()
        print(f"→ Raw Output:\n{output}")

        # --- Parse Output ---
        try:
            # Basic cleanup
            if output.startswith("```json"):
                output = output[7:]
            elif output.startswith("```"):
                 output = output[3:]
            if output.endswith("```"):
                output = output[:-3]
            output = output.strip()

            parsed = json.loads(output)

            # Basic validation
            if isinstance(parsed, dict) and "rules" in parsed and isinstance(parsed["rules"], list):
                 extracted_logic.append({"sentence": sentence, "logic": parsed})
                 print("→ Status: Successfully parsed valid JSON structure")
            else:
                 print("→ Status: Parsed JSON but missing 'rules' array or invalid structure.")
                 extracted_logic.append({"sentence": sentence, "logic_raw": output, "parse_error": "Parsed JSON structure mismatch (expected {'rules': [...]})"})

        except json.JSONDecodeError as json_e:
            print(f"→ Status: Failed to parse JSON - {json_e}")
            extracted_logic.append({"sentence": sentence, "logic_raw": output, "parse_error": str(json_e)})
        except Exception as parse_e:
            print(f"→ Status: Error during parsing/handling - {parse_e}")
            extracted_logic.append({"sentence": sentence, "logic_raw": output, "parse_error": str(parse_e)})

        time.sleep(1.2)

    # --- Error Handling based on dir(cohere.errors) ---
    except TooManyRequestsError as e:
        request_count += 1
        print(f"→ Status: Cohere Rate Limit Error (429) - {e}. Sleeping for {SLEEP_TIME_SECONDS} seconds...")
        extracted_logic.append({"sentence": sentence, "error": str(e), "error_type": "TooManyRequestsError"})
        time.sleep(SLEEP_TIME_SECONDS) # Sleep when rate limited

    except BadRequestError as e:
        request_count += 1
        print(f"→ Status: Cohere Bad Request Error (400) - {e}. Check prompt, model parameters, or JSON schema.")
        extracted_logic.append({"sentence": sentence, "error": str(e), "error_type": "BadRequestError"})
        # If this error persists, there might be another schema issue or a problem the model can't handle.
        # Consider stopping if this error repeats many times.
        time.sleep(2) # Short sleep after bad request

    except (UnauthorizedError, ForbiddenError) as e:
        request_count += 1
        print(f"→ Status: Cohere Authentication/Authorization Error (401/403) - {e}. Check API Key.")
        extracted_logic.append({"sentence": sentence, "error": str(e), "error_type": type(e).__name__})
        exit(f"Exiting due to Authentication/Authorization Error: {e}")

    except (InternalServerError, ServiceUnavailableError) as e:
        request_count += 1
        print(f"→ Status: Cohere Server Error ({type(e).__name__}) - {e}. Waiting before retry...")
        extracted_logic.append({"sentence": sentence, "error": str(e), "error_type": type(e).__name__})
        time.sleep(15) # Wait longer for server-side issues

    except Exception as e:
        request_count += 1
        error_type_name = type(e).__name__
        print(f"→ Status: Unexpected General Error - {error_type_name}: {e}")
        extracted_logic.append({"sentence": sentence, "error": str(e), "error_type": "GeneralError - " + error_type_name})
        time.sleep(2)


# --- Save Results ---
try:
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        json.dump(extracted_logic, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Successfully finished processing {total_sentences} sentences.")
    print(f"Results saved to {OUTPUT_FILENAME}")
except Exception as e:
    print(f"\n❌ Error writing output file '{OUTPUT_FILENAME}': {e}")