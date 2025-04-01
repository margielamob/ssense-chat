import cohere
import json
import time
import os

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(COHERE_API_KEY)

cleaned_sentences = [
    "Items must be in original condition, and all packaging materials, accessories and applicable tags must be returned in order to be eligible for a refund.",
    "The return must be requested within 30 calendar days of the delivery date.",
    "Lingerie, hosiery, underwear, swimsuits, and bikini bottoms cannot be worn and must be returned with the original hygienic protection sticker still intact to be eligible for a refund.",
    # Add more...
]

# Prompt template
def make_prompt(sentence):
    return f"""You are an AI assistant converting return policy sentences into structured symbolic logic.

Use the following schema:
- returnWindow(item) → within(X, days)
- returnEligibility(item) → conditions
- finalSale(item) → category
- itemCondition(item) → [conditions]
- packaging(item) → includes, intact
- refundIssued(item) → if qualityCheck(passed)

Example:
Sentence: "The return must be requested within 30 calendar days of the delivery date."
→ JSON:
{{
  "rule": "returnWindow",
  "conditions": {{
    "within": {{
      "value": 30,
      "unit": "days"
    }}
  }}
}}

Now convert this sentence:
"{sentence}"

→ JSON:
"""

# Store results
extracted_logic = []

# Cohere generation loop
for i, sentence in enumerate(cleaned_sentences):
    prompt = make_prompt(sentence)

    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
            stop_sequences=["\n\n"]
        )
        output = response.generations[0].text.strip()
        print(f"\n[{i+1}] Sentence: {sentence}\n→ Output:\n{output}\n")
        try:
            parsed = json.loads(output)
            extracted_logic.append({"sentence": sentence, "logic": parsed})
        except json.JSONDecodeError:
            extracted_logic.append({"sentence": sentence, "logic_raw": output})

        time.sleep(1)  # Be nice to the API

    except Exception as e:
        print(f"[{i+1}] Error: {e}")
        extracted_logic.append({"sentence": sentence, "error": str(e)})

# Optional: Save to file
with open("cohere_extracted_rules.json", "w") as f:
    json.dump(extracted_logic, f, indent=2)
