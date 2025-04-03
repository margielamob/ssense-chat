import requests
from bs4 import BeautifulSoup
import re
import json

url = "https://www.ssense.com/en-ca/customer-service/return-policy"
headers = {
    "User-Agent": "Mozilla/5.0",
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

raw_paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

cleaned_sentences = []
for para in raw_paragraphs:
    split_sents = re.split(r'(?<=\.)\s+(?=[A-Z])', para)
    cleaned_sentences.extend([s.strip() for s in split_sents if s.strip()])

with open("cleaned_sentences.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_sentences, f, indent=2, ensure_ascii=False)

print(f"✅ Extracted {len(cleaned_sentences)} sentences and saved to cleaned_sentences.json")