import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from pyswip import Prolog

load_dotenv()
client = OpenAI()  

# Load prompts
with open("nlu_prompt.txt") as f:
    nlu_prompt = f.read()

with open("nlg_prompt.txt") as f:
    nlg_prompt = f.read()

# Initialize Prolog engine
prolog = Prolog()
prolog.consult("ssense_policy.pl")

# Ask user for input
user_question = input("Ask a return policy question: ")

# STEP 1 — NLU (NL → JSON Query)
nlu_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": nlu_prompt},
        {"role": "user", "content": user_question}
    ],
    temperature=0.2
)

# --- Clean & Parse GPT JSON output (NLU) ---
raw_nlu_output = nlu_response.choices[0].message.content.strip()

# Remove Markdown formatting if GPT added it (e.g., ```json ... ```)
if raw_nlu_output.startswith("```"):
    raw_nlu_output = raw_nlu_output.strip("`").strip()
    if raw_nlu_output.startswith("json"):
        raw_nlu_output = raw_nlu_output[4:].strip()

try:
    nlu_json = json.loads(raw_nlu_output)
    predicate = nlu_json["predicate"]
    args = nlu_json["args"]
except Exception as e:
    print("\n❌ Failed to parse NLU response:", e)
    print(nlu_response.choices[0].message.content)
    exit(1)


# STEP 2 — Build and Run Prolog Query
arg_values = list(args.values())
query_term = f"{predicate}({', '.join(map(repr, arg_values + ['Result']))})"

try:
    result_list = list(prolog.query(query_term, maxresult=1))
    result_value = result_list[0]["Result"] if result_list else None
except Exception as e:
    print("\n❌ Prolog query failed:", e)
    print("Query attempted:", query_term)
    exit(1)

# STEP 3 — NLG (JSON + User Q → Friendly Answer)
kb_result = {
    "predicate": predicate,
    "args": args,
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
print("\n🧠 Assistant:")
print(final_answer)
