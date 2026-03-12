import json
import chromadb
from sentence_transformers import SentenceTransformer

MATERNITY_SUMMARY = """West Pakistan Maternity Benefit Ordinance 1958 - Key Entitlements

MATERNITY BENEFIT ENTITLEMENT (Section 4):
Every woman employed in an establishment is entitled to maternity benefit at the rate of her last paid wages for:
- 6 weeks immediately before delivery
- 6 weeks after delivery
- Total: 12 weeks of maternity benefit

ELIGIBILITY CONDITION: Woman must have been employed with the same employer for at least 4 months immediately before delivery.

TOTAL BENEFIT PERIOD (Section 5):
Employer shall pay maternity benefit for 12 weeks total. Payment can be made:
- 6 weeks before delivery + remainder after, OR
- Full 12 weeks after delivery within 48 hours of proof of delivery.

PROHIBITION ON WORK AFTER DELIVERY (Section 3):
No employer shall employ a woman, and no woman shall work, in any establishment during the 6 weeks following delivery.

PROTECTION FROM DISMISSAL (Section 7):
- Employer cannot give notice of dismissal to a woman while she is on maternity absence.
- Notice of dismissal given without sufficient cause within 6 months before delivery does not deprive her of maternity benefit.

SCOPE: Applies to all establishments — industrial, commercial, or otherwise — throughout Pakistan.

EMPLOYER PENALTY (Section 9): Fine up to Rs. 500 for contravention."""

new_chunk = {
    "chunk_id": "federal_1958_maternity_benefit_summary_manual",
    "province": "Federal",
    "law": "Maternity Benefit Ordinance",
    "year": 1958,
    "section_number": "summary",
    "text": MATERNITY_SUMMARY,
    "source_file": "THE WEST PAKISTAN MATERNITY BENEFIT ORDINANCE,1958.pdf",
    "source_type": "manual_summary"
}

with open("extracted_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

chunks.append(new_chunk)

with open("extracted_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"Total chunks: {len(chunks)}")

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("labor_laws")

embedding = model.encode(new_chunk["text"]).tolist()
collection.add(
    ids=[new_chunk["chunk_id"]],
    embeddings=[embedding],
    documents=[new_chunk["text"]],
    metadatas=[{
        "province": new_chunk["province"],
        "law": new_chunk["law"],
        "year": new_chunk["year"],
        "section_number": new_chunk["section_number"]
    }]
)
print("Indexed summary chunk.")

# Test
queries = ["maternity leave entitlement", "maternity benefit how many weeks", "pregnancy leave rights"]
for q in queries:
    emb = model.encode(q).tolist()
    results = collection.query(query_embeddings=[emb], n_results=1)
    score = 1 - results["distances"][0][0]
    law = results["metadatas"][0][0]["law"]
    print(f"[{score:.3f}] {q} → {law}")