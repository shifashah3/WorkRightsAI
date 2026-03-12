import json
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

with open("extracted_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Fix ALL chunk IDs to be unique by adding global index
for i, chunk in enumerate(chunks):
    base_id = f"{chunk['province'].lower()}_{chunk['year']}_{chunk['law'][:20].replace(' ', '_')}_{chunk['section_number']}"
    chunk["chunk_id"] = f"{base_id}_{i}"

with open("extracted_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"✅ Fixed {len(chunks)} chunk IDs")

# Re-index
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")

client.delete_collection("labor_laws")
collection = client.create_collection(
    name="labor_laws",
    metadata={"hnsw:space": "cosine"}
)

BATCH_SIZE = 50
for i in tqdm(range(0, len(chunks), BATCH_SIZE)):
    batch = chunks[i:i+BATCH_SIZE]
    texts = [c["text"] for c in batch]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()
    collection.add(
        ids=[c["chunk_id"] for c in batch],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{
            "province": c["province"],
            "law": c["law"],
            "year": str(c["year"]),
            "section_number": c["section_number"],
            "source_file": c["source_file"]
        } for c in batch]
    )

print(f"✅ Done. Total indexed: {collection.count()} chunks")