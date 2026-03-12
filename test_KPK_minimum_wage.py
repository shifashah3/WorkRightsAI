# import chromadb
# from sentence_transformers import SentenceTransformer

# model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# client = chromadb.PersistentClient(path="./chroma_db")
# collection = client.get_collection("labor_laws")

# # Check 1: what does the KPK minimum wage chunk actually contain?
# print("=" * 60)
# print("KPK MINIMUM WAGE CHUNKS — DIRECT LOOKUP")
# print("=" * 60)

# results = collection.get(
#     where={"law": "KPK Minimum Wages Notification"},
#     include=["documents", "metadatas"]
# )

# for i, doc in enumerate(results["documents"]):
#     print(f"\nChunk {i+1}")
#     print(f"Metadata: {results['metadatas'][i]}")
#     print(f"Text: {doc[:500]}")
#     print("-" * 40)

# # Check 2: what score does it actually get for this query?
# print("\n" + "=" * 60)
# print("SIMILARITY SCORE FOR KPK MINIMUM WAGE QUERY")
# print("=" * 60)

# embedding = model.encode("minimum wage KPK").tolist()
# results2 = collection.query(
#     query_embeddings=[embedding],
#     n_results=5,
#     where={"province": "KPK"},
#     include=["documents", "metadatas", "distances"]
# )

# for i in range(len(results2["documents"][0])):
#     score = round(1 - results2["distances"][0][i], 3)
#     meta = results2["metadatas"][0][i]
#     print(f"\nScore: {score} | Law: {meta['law']} | Section: {meta['section_number']}")
#     print(f"Text: {results2['documents'][0][i][:200]}")

import json

with open("extracted_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Fix the garbage OCR chunk
for chunk in chunks:
    if chunk["law"] == "KPK Minimum Wages Notification" and chunk["section_number"] == "1":
        chunk["text"] = """GOVERNMENT OF KHYBER PAKHTUNKHWA
LABOUR DEPARTMENT
NOTIFICATION
Peshawar, Dated 10/09/2025

In exercise of the powers conferred by clause (ii) of sub-section (1) of section 6 of the 
Khyber Pakhtunkhwa Minimum Wages Act, 2013, the Government of Khyber Pakhtunkhwa 
hereby revises the minimum wages for workers in industrial and commercial establishments in KPK.

MINIMUM WAGES TABLE (Effective 2025):

Category: Adult, unskilled, juvenile and adolescent workers employed in industrial 
and commercial establishments, whether registered or unregistered, located in the 
Province of Khyber Pakhtunkhwa.

Minimum Rates of Wages:
- Per day (8 hours of work): Rs. 1,538.46
- Per month (26 working days): Rs. 40,000

(Rupees Forty Thousand only per month)"""
        print("✅ Fixed KPK chunk 1")

# Also add as a separate dedicated chunk for better retrieval
new_chunk = {
    "chunk_id": "kpk_2025_minimum_wage_table_manual",
    "province": "KPK",
    "law": "KPK Minimum Wages Notification",
    "year": 2025,
    "section_number": "table",
    "text": """KPK Minimum Wage 2025 - Khyber Pakhtunkhwa Minimum Wages Notification

The Government of Khyber Pakhtunkhwa has set the following minimum wages effective 2025:

Category: All adult, unskilled, juvenile and adolescent workers in industrial and 
commercial establishments in Khyber Pakhtunkhwa (KPK).

Minimum wage rates:
- Daily rate (8 hours): Rs. 1,538.46 per day
- Monthly rate (26 working days): Rs. 40,000 per month

No employer in KPK may pay below these rates. Existing wages higher than minimum 
wages shall not be reduced.""",
    "source_file": "KPK-Minimum-Wages-Notification-2025.pdf",
    "source_type": "manual_correction"
}

chunks.append(new_chunk)
print("✅ Added dedicated wage table chunk")

with open("extracted_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"✅ Saved. Total chunks: {len(chunks)}")