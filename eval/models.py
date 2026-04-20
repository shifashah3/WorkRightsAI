"""
Adapters for querying different LLM providers.
All free-tier APIs that can serve as comparison baselines.
"""

import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

TIMEOUT = 45  # seconds
MODEL_MAX_RETRIES = 3
MODEL_BASE_DELAY  = 10  # doubles each retry


def _post_with_backoff(url: str, headers: dict, payload: dict, label: str) -> requests.Response:
    """POST with exponential backoff on 429/5xx."""
    delay = MODEL_BASE_DELAY
    for attempt in range(MODEL_MAX_RETRIES):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
            if resp.status_code in (429, 500, 502, 503, 504):
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else delay
                print(f"    [{label}] HTTP {resp.status_code} — waiting {wait:.0f}s (attempt {attempt+1})")
                time.sleep(wait)
                delay *= 2
                continue
            return resp
        except requests.exceptions.RequestException as e:
            if attempt < MODEL_MAX_RETRIES - 1:
                print(f"    [{label}] Error: {e} — retrying in {delay}s")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    # Final attempt
    return requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)


# ── Pakistan Labour RAG (your system via FastAPI) ─────────────────────────────
class RAGModel:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.name = "Pakistan-Labour-RAG"
        self.base_url = base_url

    def query(self, prompt: str, province: Optional[str] = None) -> str:
        try:
            payload = {"message": prompt, "province": province, "history": []}
            resp = requests.post(
                f"{self.base_url}/api/chat", json=payload, timeout=TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()["answer"]
        except Exception as e:
            return f"[ERROR] RAG model unavailable: {e}"


# ── Groq (free tier — llama3, gemma, mistral) ─────────────────────────────────
class GroqModel:
    def __init__(self, model_id: str = "llama-3.3-70b-versatile"):
        self.name = f"Groq/{model_id}"
        self.model_id = model_id
        self.api_key = os.getenv("GROQ_API_KEY")

    def query(self, prompt: str, province: Optional[str] = None) -> str:
        if not self.api_key:
            return "[ERROR] GROQ_API_KEY not set"
        try:
            system = (
                "You are a knowledgeable assistant on Pakistan labour law. "
                "Answer questions accurately based on Pakistani legislation. "
                "Be clear about limitations. Do not give harmful or illegal advice."
            )
            full_prompt = f"[Province: {province}]\n{prompt}" if province else prompt

            resp = _post_with_backoff(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                payload={
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": full_prompt},
                    ],
                    "max_tokens": 512,
                    "temperature": 0,
                },
                label=self.name,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[ERROR] Groq: {e}"


# ── Together AI (free tier) ───────────────────────────────────────────────────
class TogetherModel:
    def __init__(self, model_id: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"):
        self.name = f"Together/{model_id.split('/')[-1]}"
        self.model_id = model_id
        self.api_key = os.getenv("TOGETHER_API_KEY")

    def query(self, prompt: str, province: Optional[str] = None) -> str:
        if not self.api_key:
            return "[ERROR] TOGETHER_API_KEY not set"
        try:
            system = (
                "You are a knowledgeable assistant on Pakistan labour law. "
                "Answer accurately based on Pakistani legislation. "
                "Do not give harmful or illegal advice."
            )
            full_prompt = prompt
            if province:
                full_prompt = f"[Province: {province}]\n{prompt}"

            resp = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": full_prompt},
                    ],
                    "max_tokens": 512,
                    "temperature": 0,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[ERROR] Together: {e}"


# ── Google Gemini (free tier) ─────────────────────────────────────────────────
class GeminiModel:
    def __init__(self, model_id: str = "gemini-1.5-flash"):
        self.name = f"Gemini/{model_id}"
        self.model_id = model_id
        self.api_key = os.getenv("GEMINI_API_KEY")

    def query(self, prompt: str, province: Optional[str] = None) -> str:
        if not self.api_key:
            return "[ERROR] GEMINI_API_KEY not set"
        try:
            system_prefix = (
                "You are a knowledgeable assistant on Pakistan labour law. "
                "Answer accurately. Do not give harmful or illegal advice.\n\n"
            )
            full_prompt = system_prefix + (f"[Province: {province}]\n{prompt}" if province else prompt)

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.model_id}:generateContent?key={self.api_key}"
            )
            resp = _post_with_backoff(
                url,
                headers={"Content-Type": "application/json"},
                payload={"contents": [{"parts": [{"text": full_prompt}]}]},
                label=self.name,
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            return f"[ERROR] Gemini: {e}"


def get_models():
    """Return all models to evaluate. Comment out unavailable ones."""
    return [
        RAGModel(),
        GroqModel("llama-3.3-70b-versatile"),   # baseline: same base model, no RAG
        GroqModel("gemma2-9b-it"),               # smaller open model
        GeminiModel("gemini-1.5-flash"),         # Google free tier
        # TogetherModel(),                       # uncomment if you have Together key
    ]