import requests
from bs4 import BeautifulSoup
import re

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

for idx, sentence in enumerate(cleaned_sentences):
    print(f"[{idx+1}] {sentence}")
