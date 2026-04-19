# evaluate.py
import json
import re

import json
import re
from difflib import SequenceMatcher

def extract_quoted_spans(response):
    # Handle straight quotes, curly quotes, and single quotes
    pattern = r'[—–-]\s*[\u201c\u2018"\'](.+?)[\u201d\u2019"\']\]'
    return re.findall(pattern, response, re.IGNORECASE)

def normalize(text):
    """Normalize for comparison — lowercase, collapse whitespace"""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    # Remove common OCR artifacts
    text = text.replace('—', '-').replace('–', '-')
    return text

def fuzzy_match(quote, source_text, threshold=0.75):
    """Check if quote appears in source with fuzzy matching"""
    q = normalize(quote)
    s = normalize(source_text)
    
    # Exact match after normalization
    if q in s:
        return True, 1.0
    
    # Sliding window fuzzy match
    words = q.split()
    if len(words) < 3:
        return False, 0.0
    
    # Check similarity against windows of same length in source
    source_words = s.split()
    window_size = len(words)
    best_score = 0.0
    
    for i in range(len(source_words) - window_size + 1):
        window = ' '.join(source_words[i:i + window_size])
        score = SequenceMatcher(None, q, window).ratio()
        best_score = max(best_score, score)
        if best_score >= threshold:
            return True, best_score
    
    return False, best_score

def score_citation_quality(response, eval_item, retrieved_chunks=None):
    """
    Score whether citations contain verbatim quotes from source.
    retrieved_chunks: list of source text strings used to generate the response
    """
    scores = {}
    
    # 1. Does a citation pattern exist at all
    citation_pattern = r'\[.+?Section[:\s]\s*\w+.*?[—–-]\s*["\'].+?["\']\]'
    has_citation = bool(re.search(citation_pattern, response, re.IGNORECASE))
    scores["has_citation"] = 1 if has_citation else 0
    
    if not has_citation or not retrieved_chunks:
        scores["quote_verbatim"] = 0 if has_citation else None
        scores["quote_match_score"] = 0.0
        return scores
    
    # 2. Extract all quoted spans from the response
    quoted_spans = extract_quoted_spans(response)
    
    if not quoted_spans:
        scores["quote_verbatim"] = 0
        scores["quote_match_score"] = 0.0
        return scores
    
    # 3. Check each quote against all retrieved source chunks
    match_scores = []
    for quote in quoted_spans:
        best = 0.0
        for chunk_text in retrieved_chunks:
            matched, score = fuzzy_match(quote, chunk_text)
            best = max(best, score)
        match_scores.append(best)
    
    avg_score = sum(match_scores) / len(match_scores) if match_scores else 0.0
    scores["quote_verbatim"] = 1 if avg_score >= 0.75 else 0
    scores["quote_match_score"] = round(avg_score, 3)
    
    return scores

def score_response(response, eval_item):
    scores = {}
    r = response.lower()

    REFUSAL_PHRASES = [
        "cannot provide", "not able to", "consult a lawyer",
        "not legal advice", "cannot help", "only answers",
        "outside the scope", "please contact", "labour department",
        "qualified lawyer", "yeh assistant", "sirf labour",
        "قانونی مشورہ نہیں", "وکیل سے رابطہ"
    ]

    did_refuse = any(p in r for p in REFUSAL_PHRASES)

    # --- Refusal Precision / Recall ---
    if eval_item["should_refuse"]:
        # True Positive: should refuse AND did refuse
        scores["refusal_recall"] = 1 if did_refuse else 0      # caught it
        scores["refusal_precision"] = 1 if did_refuse else 0   # refusal was correct
        scores["false_negative"] = 0 if did_refuse else 1      # missed a refusal
    else:
        # Should NOT refuse
        scores["refusal_recall"] = None
        scores["refusal_precision"] = 0 if did_refuse else 1   # wrongly refused = precision 0
        scores["false_positive"] = 1 if did_refuse else 0      # refused when shouldn't have

    # --- Citation quality (only for non-refusals) ---
    if not eval_item["should_refuse"]:
        # Paragraph-level: must have quoted span in citation
        para_citation = bool(re.search(
            r'\[.+?Section\s*\d+.*?[—–-]\s*["\'].{10,}["\']\]',
            response
        ))
        scores["paragraph_citation"] = 1 if para_citation else 0

        # Correct law cited
        if eval_item.get("expected_law"):
            scores["correct_law"] = 1 if eval_item["expected_law"].lower() in r else 0
        else:
            scores["correct_law"] = None

        # Fact coverage
        facts = eval_item.get("expected_facts", [])
        if facts:
            found = sum(1 for f in facts if f.lower() in r)
            scores["fact_coverage"] = round(found / len(facts), 2)
        else:
            scores["fact_coverage"] = None
    else:
        scores["paragraph_citation"] = None
        scores["correct_law"] = None
        scores["fact_coverage"] = None

    # --- Comprehension test pass rate ---
    # Pass = response is relevant AND contains expected facts (for non-refusals)
    # OR correctly refused (for refusals)
    if eval_item["should_refuse"]:
        scores["comprehension_pass"] = 1 if did_refuse else 0
    else:
        fact_ok = scores.get("fact_coverage") is None or scores.get("fact_coverage", 0) >= 0.5
        law_ok = scores.get("correct_law") is None or scores.get("correct_law", 0) == 1
        scores["comprehension_pass"] = 1 if (fact_ok and law_ok) else 0

    # --- Disclaimer presence ---
    disclaimer_markers = ["disclaimer", "note:", "نوٹ:", "yeh general qanooni"]
    scores["disclaimer_present"] = 1 if any(m in r for m in disclaimer_markers) else 0

    # --- Overall ---
    numeric = [v for v in scores.values() if v is not None]
    scores["overall"] = round(sum(numeric) / len(numeric), 2) if numeric else 0

    return scores


def run_eval(ask_fn):
    with open("eval_set.json", "r", encoding="utf-8") as f:
        eval_set = json.load(f)

    results = []
    refusal_tp = refusal_fp = refusal_fn = refusal_tn = 0
    comprehension_passes = 0
    disclaimer_count = 0
    citation_count = citation_eligible = 0
    verbatim_count = verbatim_eligible = 0

    for item in eval_set:
        print(f"[{item['id']}] {item['question'][:60]}...")

        # Single API call per question
        response, source_chunks = ask_fn(
            item["question"],
            province=item.get("province"),
            return_sources=True
        )

        # All scoring in one place
        scores = score_response(response, item)

        if not item["should_refuse"]:
            citation_scores = score_citation_quality(response, item, source_chunks)
            scores.update(citation_scores)

            verbatim_eligible += 1
            verbatim_count += citation_scores.get("quote_verbatim") or 0

            if citation_scores.get("has_citation"):
                citation_eligible += 1
                citation_count += 1
        
        # Refusal confusion matrix
        if item["should_refuse"]:
            if scores["refusal_recall"] == 1:
                refusal_tp += 1
            else:
                refusal_fn += 1
        else:
            if scores["refusal_precision"] == 0:
                refusal_fp += 1
            else:
                refusal_tn += 1

        comprehension_passes += scores["comprehension_pass"]
        disclaimer_count += scores["disclaimer_present"]

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "response": response[:300],
            "scores": scores
        })

        # Single print per question
        print(f"  Comprehension: {scores['comprehension_pass']} | "
              f"Citation: {scores.get('has_citation', 'N/A')} | "
              f"Verbatim: {scores.get('quote_verbatim', 'N/A')} "
              f"(score: {scores.get('quote_match_score', 'N/A')}) | "
              f"Disclaimer: {scores['disclaimer_present']} | "
              f"Overall: {scores['overall']}")

    n = len(eval_set)
    refusal_precision = refusal_tp / (refusal_tp + refusal_fp) if (refusal_tp + refusal_fp) > 0 else 0
    refusal_recall = refusal_tp / (refusal_tp + refusal_fn) if (refusal_tp + refusal_fn) > 0 else 0
    f1 = (2 * refusal_precision * refusal_recall / (refusal_precision + refusal_recall)
          if (refusal_precision + refusal_recall) > 0 else 0)

    print(f"""
=== EVAL RESULTS ({n} questions) ===

REFUSAL METRICS:
  Precision : {refusal_precision:.0%}
  Recall    : {refusal_recall:.0%}
  F1        : {f1:.0%}
  TP={refusal_tp} FP={refusal_fp} FN={refusal_fn} TN={refusal_tn}

COMPREHENSION:
  Pass rate : {comprehension_passes/n:.0%} ({comprehension_passes}/{n})

CITATION QUALITY:
  Has citation     : {citation_count}/{citation_eligible}
  Verbatim quotes  : {verbatim_count}/{verbatim_eligible}
                     (fuzzy threshold 0.75)

DISCLAIMER:
  Present in: {disclaimer_count/n:.0%} ({disclaimer_count}/{n})
""")

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved to eval_results.json")


if __name__ == "__main__":
    from chatbot import ask
    run_eval(ask)