import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import os

# load variables from .env
load_dotenv()

# Initialize
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("labor_laws")

SYSTEM_PROMPT = """You are a Pakistan Labour Rights Assistant. You help workers and employers understand their rights and obligations under Pakistani labour law.

STRICT RULES:
1. Answer ONLY based on the legal context provided to you. Do not use outside knowledge.
2. ALWAYS cite the specific law and section number for every claim you make.
3. Use this citation format: [Law Name, Section X, Province]
4. If the provided context does not contain enough information to answer, say: "I could not find specific information on this in my current database. Please consult a lawyer or contact your provincial labour department."
5. NEVER give personalized legal advice. Never say "you should" or "you will win". Stick to what the law says.
6. Keep answers in plain, simple language. Avoid legal jargon where possible.
7. If the question involves a specific province, prioritize that province's laws.
8. At the end of every answer, add: "Note: This is general legal information, not legal advice. For your specific situation, consult a qualified lawyer or contact your provincial Labour Department."

FORMAT:
- Start with a direct answer in 1-2 sentences
- Then explain with citations
- End with the note above"""

def retrieve_context(query, province=None, n=5):
    embedding = model.encode(query).tolist()
    where = {"province": province} if province else None
    
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    context_parts = []
    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        score = round(1 - results["distances"][0][i], 3)
        
        if score < 0.25:  # skip low relevance chunks
            continue
            
        context_parts.append(
            f"[{meta['law']}, Section {meta['section_number']}, {meta['province']}]\n{doc}"
        )
    
    return "\n\n---\n\n".join(context_parts)

def ask(query, province=None, conversation_history=[]):
    # Retrieve relevant chunks
    context = retrieve_context(query, province)
    if not context:
        context = retrieve_context(query, province=None)
    
    # Build message with context injected
    user_message = f"""Question: {query}
{f'Province: {province}' if province else ''}

Relevant legal provisions from Pakistani labour law:
{context}

Please answer the question based strictly on the above legal provisions."""

    # Add to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
   
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # free and strong
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        max_tokens=1024
    )

    answer = response.choices[0].message.content
    # Add assistant response to history
    conversation_history.append({
        "role": "assistant",
        "content": answer
    })
    
    return answer, conversation_history

def run_chatbot():
    print("=" * 60)
    print("Pakistan Labour Rights Assistant")
    print("=" * 60)
    print("Type 'quit' to exit")
    print("Type 'province:Sindh' (or Punjab/KPK/Balochistan/Federal)")
    print("to filter results by province\n")
    
    history = []
    current_province = None
    
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'quit':
            break
        
        # Check for province filter
        if user_input.lower().startswith("province:"):
            current_province = user_input.split(":")[1].strip()
            print(f"Province set to: {current_province}\n")
            continue
        
        if user_input.lower() == "province:clear":
            current_province = None
            print("Province filter cleared\n")
            continue
        
        print(f"\nAssistant: ", end="", flush=True)
        answer, history = ask(user_input, current_province, history)
        print(answer)
        print()

if __name__ == "__main__":
    run_chatbot()