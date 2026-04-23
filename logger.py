import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

LOG_FILE = "logs/interactions.jsonl"

def setup_logger():
    os.makedirs("logs", exist_ok=True)

def log_interaction(
    query,
    response,
    province=None,
    guardrail_status=None,
    guardrail_message=None,
    retrieval_score=None,
    retrieved_laws=None,
    guardrail_flags=None,
    response_time_ms=None
):
    entry = {
        "timestamp": datetime.now(ZoneInfo("Asia/Karachi")).isoformat(),
        "query": query,
        "province": province,
        "guardrail_status": guardrail_status,
        "guardrail_message": guardrail_message,
        "retrieval_score": retrieval_score,
        "retrieved_laws": retrieved_laws,
        "guardrail_flags": guardrail_flags or [],
        "response_time_ms": response_time_ms,
        "response": response
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")