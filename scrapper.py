import requests
from bs4 import BeautifulSoup
import re

# Step 1: Scrape the return policy page
url = "https://www.ssense.com/en-ca/customer-service/return-policy"
headers = {
    "User-Agent": "Mozilla/5.0",
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# Step 2: Extract and clean all <p> elements
raw_paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

# Step 3: Clean and split compound paragraphs into atomic sentences
cleaned_sentences = []
for para in raw_paragraphs:
    # Split on ". " followed by uppercase letter, keep period
    split_sents = re.split(r'(?<=\.)\s+(?=[A-Z])', para)
    cleaned_sentences.extend([s.strip() for s in split_sents if s.strip()])

# Step 4: Print results with numbering
for idx, sentence in enumerate(cleaned_sentences):
    print(f"[{idx+1}] {sentence}")
