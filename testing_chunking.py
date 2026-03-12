import json
import chromadb
from sentence_transformers import SentenceTransformer

# Load chunks
with open("extracted_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("labor_laws")

print("=" * 60)
print("AUTOMATED CHUNK QUALITY REPORT")
print("=" * 60)

# Test 1: Chunks with too much garbage (OCR noise indicators)
import re

def ocr_noise_score(text):
    """Count indicators of bad OCR"""
    score = 0
    # Random symbols
    score += len(re.findall(r'[|\\~\^\*]{2,}', text))
    # Broken words (single letters separated by spaces)
    score += len(re.findall(r'\b[a-z]\s[a-z]\s[a-z]\b', text))
    # Garbled sequences
    score += len(re.findall(r'[a-z]{1,2}[0-9][a-z]{1,2}', text))
    # Very short lines repeated
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    short_lines = sum(1 for l in lines if len(l) < 10)
    score += short_lines
    return score

print("\n🔴 HIGH NOISE CHUNKS (likely bad OCR):")
noisy = []
for c in chunks:
    score = ocr_noise_score(c["text"])
    if score > 10:
        noisy.append((score, c))

noisy.sort(key=lambda x: x[0], reverse=True)
for score, c in noisy[:15]:
    print(f"  Score {score:3d} | {c['law']} | Section {c['section_number']} | Province {c['province']}")
    print(f"           Preview: {c['text'][:100].strip()}")

# Test 2: Chunks that are mostly numbers (wage tables - may be unreadable)
print("\n🟡 NUMERIC/TABLE CHUNKS (wage tables, may need manual check):")
for c in chunks:
    words = c["text"].split()
    if len(words) < 50:
        continue
    numeric = sum(1 for w in words if re.match(r'^[\d,/\-\.]+$', w))
    ratio = numeric / len(words)
    if ratio > 0.3:
        print(f"  {ratio:.0%} numeric | {c['law']} | Section {c['section_number']} | {c['province']}")
        print(f"  Preview: {c['text'][:150].strip()}")
        print()

# Test 3: Run benchmark queries and check if right laws are retrieved
print("\n🔵 RETRIEVAL BENCHMARK (key questions)")
print("=" * 60)

benchmark = [
    ("what is the minimum wage in Punjab",       "Punjab",       "Minimum"),
    ("what is the minimum wage in Sindh",        "Sindh",        "Minimum"),
    ("what is the minimum wage in Balochistan",  "Balochistan",  "Minimum"),
    ("termination without notice rights",         None,           "Termination"),
    ("harassment complaint procedure",            None,           "Harassment"),
    ("overtime pay calculation",                  None,           "Factories"),
    ("maternity leave entitlement",               None,           "maternity"),
    ("annual leave how many days",                None,           "leave"),
    ("EOBI pension benefits",                     None,           "Old Age"),
    ("child labour prohibited age",               None,           "Children"),
]

for query, province, expected_keyword in benchmark:
    embedding = model.encode(query).tolist()
    where = {"province": province} if province else None
    results = collection.query(
        query_embeddings=[embedding],
        n_results=3,
        where=where,
        include=["metadatas", "distances"]
    )
    
    top_law = results["metadatas"][0][0]["law"] if results["metadatas"][0] else "NONE"
    top_score = round(1 - results["distances"][0][0], 3) if results["distances"][0] else 0
    found = expected_keyword.lower() in top_law.lower()
    
    status = "✅" if found and top_score > 0.4 else "⚠️ " if top_score > 0.4 else "❌"
    print(f"{status} [{top_score}] Q: {query[:45]:<45} → {top_law}")

print("\n✅ Report complete")