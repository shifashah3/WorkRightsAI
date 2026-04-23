import json
import chromadb
from sentence_transformers import SentenceTransformer

BALOCHISTAN_WAGE_SUMMARY = """Balochistan Minimum Wage Notification 2023 - Key Rates

MINIMUM WAGE RATES (Schedule, effective 1st July 2023):

1. Un-skilled adult workers employed in Industrial/Commercial Undertakings in Balochistan Province:
   - Per Day: Rs. 1,231/-
   - Per Month: Rs. 32,000/- (26 working days)

2. Un-skilled Juvenile/Adolescent workers employed in Industrial/Commercial Establishment:
   - Per Day: Rs. 1,231/-
   - Per Month: Rs. 32,000/- (26 working days)

SCOPE (Section I): Applies to all unskilled adult and juvenile/adolescent workers employed in all
Industrial and Commercial establishments of any sort (registered or unregistered) located in the
Province of Balochistan. Rates are applicable uniformly throughout the Province.

EFFECTIVE DATE: 1st July, 2023.

LEGAL BASIS: Issued under Section 4 of Balochistan Minimum Wages Act 2021 (Act No. X of 2021)
and Section-6(1)(a) of Balochistan Minimum Wages Act, 2021.

EQUAL PAY (Section III): A female worker of the category shall get the same minimum wages as
allowed to a male worker of the category of such work.

PIECE RATE WORKERS (Section VIII): Employers shall ensure piece rate workers earn not less than
Rs. 154/- per hour in any working day.

PAYMENT METHOD: All wages must be paid through cross Cheque/Bank transfer."""

new_chunk = {
    "chunk_id": "balochistan_2023_minimum_wage_schedule_manual",
    "province": "Balochistan",
    "law": "Balochistan Minimum Wage Notification",
    "year": 2023,
    "section_number": "schedule",
    "text": BALOCHISTAN_WAGE_SUMMARY,
    "source_file": "Balochistan_Minimum_Wage_Notification_2023.pdf",
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
print("Indexed Balochistan minimum wage chunk.")