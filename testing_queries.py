import chromadb
from sentence_transformers import SentenceTransformer

# Load
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("labor_laws")

def search(query, province=None, n=3):
    embedding = model.encode(query).tolist()
    
    where = {"province": province} if province else None
    
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    print(f"\nQuery: '{query}'")
    if province:
        print(f"Filter: {province} only")
    print("=" * 60)
    
    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        score = round(1 - results["distances"][0][i], 3)
        
        print(f"\nResult {i+1} — Score: {score}")
        print(f"Law: {meta['law']} | Province: {meta['province']} | Section: {meta['section_number']}")
        print(f"Text: {doc[:300]}")
        print("-" * 40)

# Test 5 realistic user queries
search("what happens if employer does not pay wages on time")
search("termination without notice")
search("maternity leave rights")
search("harassment at workplace how to complain")
search("minimum wage Sindh 2024", province="Sindh")