import json
import chromadb
from sentence_transformers import SentenceTransformer

PUNJAB_WAGE_TEXT = """Punjab Minimum Wages Notification 2024-25
Issued by: Government of Punjab, Labour and Human Resource Department
Effective from: 1st July 2024
Authority: Section 6, Punjab Minimum Wages Act, 2019

UNSKILLED WORKERS (all industrial and commercial establishments in Punjab):
- Rs. 37,000/- per month (26 working days)
- Rs. 1,423.07/- per day (8 working hours)

SKILLED/SEMI-SKILLED WORKERS (Appendix-A, applicable to 102 industries):
- Highly Skilled-A: Rs. 44,532/- per month
- Highly Skilled-B: Rs. 42,677/- per month
- Skilled-A: Rs. 41,815/- per month
- Skilled-B: Rs. 40,823/- per month
- Ministerial-A: Rs. 44,532/- per month
- Ministerial-B: Rs. 41,815/- per month
- Ministerial-C: Rs. 40,203/- per month
- Semi-Skilled-A: Rs. 39,088/- per month
- Semi-Skilled-B: Rs. 38,348/- per month
- Unskilled: Rs. 37,000/- per month

DEDUCTIONS ALLOWED (by agreement, in lieu of accommodation/transport provided):
- Accommodation: Rs. 459.03/- per month
- Transport: Rs. 98.28/- per month

EQUAL PAY: Women workers entitled to equal wages as men for work of equal value.
NOTE: Managerial and supervisory staff wages are left for mutual bargaining.
NOTE: Existing wages higher than these minimums shall not be reduced."""

with open("extracted_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

for chunk in chunks:
    if (chunk["province"] == "Punjab" and 
        chunk["law"] == "Minimum Wages Notification" and
        chunk["section_number"] in ["3", "5", "7"]):
        chunk["text"] = PUNJAB_WAGE_TEXT

with open("extracted_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("labor_laws")

for chunk in chunks:
    if (chunk["province"] == "Punjab" and 
        chunk["law"] == "Minimum Wages Notification" and
        chunk["section_number"] in ["3", "5", "7"]):
        embedding = model.encode(chunk["text"]).tolist()
        collection.update(ids=[chunk["chunk_id"]], embeddings=[embedding], documents=[chunk["text"]])
        print(f"Updated: {chunk['chunk_id']}")

print("Done.")