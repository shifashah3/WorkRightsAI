# WorkRightsAI — Pakistan Labour Rights Assistant

A responsible RAG-based chatbot that answers workplace rights questions using official Pakistani legal texts. Built as a Final Year Project for a Generative AI course.

---

## What it does

- Answers questions about minimum wage, termination, maternity leave, harassment, child labour, overtime, and EOBI across all Pakistani provinces
- Supports English, Roman Urdu, and Urdu script
- Cites specific law sections with verbatim quote spans — no vague references
- Refuses personal legal advice, harmful requests, and off-topic queries
- Logs every interaction for accountability and audit

---

## Tech Stack

- **LLM:** Llama 3.3 70b via Groq API
- **Embeddings:** paraphrase-multilingual-MiniLM-L12-v2 (handles English, Urdu, Roman Urdu)
- **Vector Store:** ChromaDB
- **PDF Extraction:** pdfplumber + Tesseract OCR for scanned documents
- **Framework:** Python

---

## Setup

Install dependencies:

    pip install pdfplumber chromadb sentence-transformers groq python-dotenv

Create a `.env` file in the project root:

    GROQ_API_KEY=your_key_here

Run the chatbot:

    python chatbot.py


---


## How it works

1. **Corpus:** 33 legal PDFs chunked at section level with province, law, and year metadata
2. **Retrieval:** Query is embedded and matched against 1170+ chunks using cosine similarity. Chunks below 0.40 relevance threshold are discarded.
3. **Context formatting:** Retrieved chunks are split into numbered sentences so the LLM can quote specific lines
4. **Generation:** LLM classifies intent, answers in the query language, cites verbatim
5. **Safety:** Three-layer guardrail system — keyword filters, LLM intent check inside main prompt, post-generation claim interception

---

## Legal Coverage

| Province | Laws Covered |
|---|---|
| Federal | Payment of Wages Act, Factories Act, Maternity Benefit Ordinance, EOBI Act, Employment of Children Act, Industrial Relations Act, Harassment Act, Mines Act, Workmen's Compensation Act, Shops & Establishments Ordinance, Bonded Labour Act |
| Punjab | Minimum Wages Notification 2024-25, Domestic Workers Act, Shops Ordinance, Industrial Relations Act, Standing Orders Ordinance |
| Sindh | Minimum Wage Notifications (Skilled & Unskilled), Industrial Relations Act, Shops Act, Home Based Workers Act, Harassment Act, Standing Orders Act |
| KPK | Minimum Wages Notification 2025, Payment of Wages Act, Industrial Relations Act, Shops Act, Standing Orders Act |
| Balochistan | Minimum Wage Notification 2023, Payment of Wages Act, Industrial Relations Act |

---

## Safety Features

- Refuses harmful requests (evading labour laws, underpaying workers) 
- Refuses personal legal advice and case outcome prediction
- Intercepts legal claims made without verbatim citations
- Detects prompt injection in English, Roman Urdu, and Urdu script
- Logs all interactions with guardrail status and retrieval scores

---
