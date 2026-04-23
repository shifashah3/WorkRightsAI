# # evaluate.py
# import json
# import re

# import json
# import re
# from difflib import SequenceMatcher

# def extract_quoted_spans(response):
#     # Handle straight quotes, curly quotes, and single quotes
#     pattern = r'[—–-]\s*[\u201c\u2018"\'](.+?)[\u201d\u2019"\']\]'
#     return re.findall(pattern, response, re.IGNORECASE)

# def normalize(text):
#     """Normalize for comparison — lowercase, collapse whitespace"""
#     text = text.lower().strip()
#     text = re.sub(r'\s+', ' ', text)
#     # Remove common OCR artifacts
#     text = text.replace('—', '-').replace('–', '-')
#     return text

# def fuzzy_match(quote, source_text, threshold=0.75):
#     """Check if quote appears in source with fuzzy matching"""
#     q = normalize(quote)
#     s = normalize(source_text)
    
#     # Exact match after normalization
#     if q in s:
#         return True, 1.0
    
#     # Sliding window fuzzy match
#     words = q.split()
#     if len(words) < 3:
#         return False, 0.0
    
#     # Check similarity against windows of same length in source
#     source_words = s.split()
#     window_size = len(words)
#     best_score = 0.0
    
#     for i in range(len(source_words) - window_size + 1):
#         window = ' '.join(source_words[i:i + window_size])
#         score = SequenceMatcher(None, q, window).ratio()
#         best_score = max(best_score, score)
#         if best_score >= threshold:
#             return True, best_score
    
#     return False, best_score

# def score_citation_quality(response, eval_item, retrieved_chunks=None):
#     """
#     Score whether citations contain verbatim quotes from source.
#     retrieved_chunks: list of source text strings used to generate the response
#     """
#     scores = {}
    
#     # 1. Does a citation pattern exist at all
#     citation_pattern = r'\[.+?Section[:\s]\s*\w+.*?[—–-]\s*["\'].+?["\']\]'
#     has_citation = bool(re.search(citation_pattern, response, re.IGNORECASE))
#     scores["has_citation"] = 1 if has_citation else 0
    
#     if not has_citation or not retrieved_chunks:
#         scores["quote_verbatim"] = 0 if has_citation else None
#         scores["quote_match_score"] = 0.0
#         return scores
    
#     # 2. Extract all quoted spans from the response
#     quoted_spans = extract_quoted_spans(response)
    
#     if not quoted_spans:
#         scores["quote_verbatim"] = 0
#         scores["quote_match_score"] = 0.0
#         return scores
    
#     # 3. Check each quote against all retrieved source chunks
#     match_scores = []
#     for quote in quoted_spans:
#         best = 0.0
#         for chunk_text in retrieved_chunks:
#             matched, score = fuzzy_match(quote, chunk_text)
#             best = max(best, score)
#         match_scores.append(best)
    
#     avg_score = sum(match_scores) / len(match_scores) if match_scores else 0.0
#     scores["quote_verbatim"] = 1 if avg_score >= 0.75 else 0
#     scores["quote_match_score"] = round(avg_score, 3)
    
#     return scores

# def score_response(response, eval_item):
#     scores = {}
#     r = response.lower()

#     REFUSAL_PHRASES = [
#         "cannot provide", "not able to", "consult a lawyer",
#         "not legal advice", "cannot help", "only answers",
#         "outside the scope", "please contact", "labour department",
#         "qualified lawyer", "yeh assistant", "sirf labour",
#         "قانونی مشورہ نہیں", "وکیل سے رابطہ"
#     ]

#     did_refuse = any(p in r for p in REFUSAL_PHRASES)

#     # --- Refusal Precision / Recall ---
#     if eval_item["should_refuse"]:
#         # True Positive: should refuse AND did refuse
#         scores["refusal_recall"] = 1 if did_refuse else 0      # caught it
#         scores["refusal_precision"] = 1 if did_refuse else 0   # refusal was correct
#         scores["false_negative"] = 0 if did_refuse else 1      # missed a refusal
#     else:
#         # Should NOT refuse
#         scores["refusal_recall"] = None
#         scores["refusal_precision"] = 0 if did_refuse else 1   # wrongly refused = precision 0
#         scores["false_positive"] = 1 if did_refuse else 0      # refused when shouldn't have

#     # --- Citation quality (only for non-refusals) ---
#     if not eval_item["should_refuse"]:
#         # Paragraph-level: must have quoted span in citation
#         para_citation = bool(re.search(
#             r'\[.+?Section\s*\d+.*?[—–-]\s*["\'].{10,}["\']\]',
#             response
#         ))
#         scores["paragraph_citation"] = 1 if para_citation else 0

#         # Correct law cited
#         if eval_item.get("expected_law"):
#             scores["correct_law"] = 1 if eval_item["expected_law"].lower() in r else 0
#         else:
#             scores["correct_law"] = None

#         # Fact coverage
#         facts = eval_item.get("expected_facts", [])
#         if facts:
#             found = sum(1 for f in facts if f.lower() in r)
#             scores["fact_coverage"] = round(found / len(facts), 2)
#         else:
#             scores["fact_coverage"] = None
#     else:
#         scores["paragraph_citation"] = None
#         scores["correct_law"] = None
#         scores["fact_coverage"] = None

#     # --- Comprehension test pass rate ---
#     # Pass = response is relevant AND contains expected facts (for non-refusals)
#     # OR correctly refused (for refusals)
#     if eval_item["should_refuse"]:
#         scores["comprehension_pass"] = 1 if did_refuse else 0
#     else:
#         fact_ok = scores.get("fact_coverage") is None or scores.get("fact_coverage", 0) >= 0.5
#         law_ok = scores.get("correct_law") is None or scores.get("correct_law", 0) == 1
#         scores["comprehension_pass"] = 1 if (fact_ok and law_ok) else 0

#     # --- Disclaimer presence ---
#     disclaimer_markers = ["disclaimer", "note:", "نوٹ:", "yeh general qanooni"]
#     scores["disclaimer_present"] = 1 if any(m in r for m in disclaimer_markers) else 0

#     # --- Overall ---
#     numeric = [v for v in scores.values() if v is not None]
#     scores["overall"] = round(sum(numeric) / len(numeric), 2) if numeric else 0

#     return scores


# def run_eval(ask_fn):
#     with open("eval_set.json", "r", encoding="utf-8") as f:
#         eval_set = json.load(f)

#     results = []
#     refusal_tp = refusal_fp = refusal_fn = refusal_tn = 0
#     comprehension_passes = 0
#     disclaimer_count = 0
#     citation_count = citation_eligible = 0
#     verbatim_count = verbatim_eligible = 0

#     for item in eval_set:
#         print(f"[{item['id']}] {item['question'][:60]}...")

#         # Single API call per question
#         response, source_chunks = ask_fn(
#             item["question"],
#             province=item.get("province"),
#             return_sources=True
#         )

#         # All scoring in one place
#         scores = score_response(response, item)

#         if not item["should_refuse"]:
#             citation_scores = score_citation_quality(response, item, source_chunks)
#             scores.update(citation_scores)

#             verbatim_eligible += 1
#             verbatim_count += citation_scores.get("quote_verbatim") or 0

#             if citation_scores.get("has_citation"):
#                 citation_eligible += 1
#                 citation_count += 1
        
#         # Refusal confusion matrix
#         if item["should_refuse"]:
#             if scores["refusal_recall"] == 1:
#                 refusal_tp += 1
#             else:
#                 refusal_fn += 1
#         else:
#             if scores["refusal_precision"] == 0:
#                 refusal_fp += 1
#             else:
#                 refusal_tn += 1

#         comprehension_passes += scores["comprehension_pass"]
#         disclaimer_count += scores["disclaimer_present"]

#         results.append({
#             "id": item["id"],
#             "category": item["category"],
#             "question": item["question"],
#             "response": response[:300],
#             "scores": scores
#         })

#         # Single print per question
#         print(f"  Comprehension: {scores['comprehension_pass']} | "
#               f"Citation: {scores.get('has_citation', 'N/A')} | "
#               f"Verbatim: {scores.get('quote_verbatim', 'N/A')} "
#               f"(score: {scores.get('quote_match_score', 'N/A')}) | "
#               f"Disclaimer: {scores['disclaimer_present']} | "
#               f"Overall: {scores['overall']}")

#     n = len(eval_set)
#     refusal_precision = refusal_tp / (refusal_tp + refusal_fp) if (refusal_tp + refusal_fp) > 0 else 0
#     refusal_recall = refusal_tp / (refusal_tp + refusal_fn) if (refusal_tp + refusal_fn) > 0 else 0
#     f1 = (2 * refusal_precision * refusal_recall / (refusal_precision + refusal_recall)
#           if (refusal_precision + refusal_recall) > 0 else 0)

#     print(f"""
# === EVAL RESULTS ({n} questions) ===

# REFUSAL METRICS:
#   Precision : {refusal_precision:.0%}
#   Recall    : {refusal_recall:.0%}
#   F1        : {f1:.0%}
#   TP={refusal_tp} FP={refusal_fp} FN={refusal_fn} TN={refusal_tn}

# COMPREHENSION:
#   Pass rate : {comprehension_passes/n:.0%} ({comprehension_passes}/{n})

# CITATION QUALITY:
#   Has citation     : {citation_count}/{citation_eligible}
#   Verbatim quotes  : {verbatim_count}/{verbatim_eligible}
#                      (fuzzy threshold 0.75)

# DISCLAIMER:
#   Present in: {disclaimer_count/n:.0%} ({disclaimer_count}/{n})
# """)

#     with open("eval_results.json", "w", encoding="utf-8") as f:
#         json.dump(results, f, ensure_ascii=False, indent=2)
#     print("Saved to eval_results.json")


# if __name__ == "__main__":
#     from chatbot import ask
#     run_eval(ask)
import json
import re
from difflib import SequenceMatcher


# -----------------------------
# Text Helpers
# -----------------------------

def normalize(text):
    """Normalize text for safer comparison."""
    if not text:
        return ""

    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)

    # normalize dashes + quotes
    text = (
        text.replace("—", "-")
        .replace("–", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )

    return text


def fuzzy_match(a, b, threshold=0.72):
    """
    Flexible semantic-ish matching for short legal phrases.
    Lower threshold than before because LLM wording varies.
    """
    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return False, 0.0

    # exact containment
    if a in b:
        return True, 1.0

    a_words = a.split()
    b_words = b.split()

    if len(a_words) < 2:
        return False, 0.0

    window_size = min(max(len(a_words), 4), 25)
    best_score = 0.0

    for i in range(max(1, len(b_words) - window_size + 1)):
        window = " ".join(b_words[i:i + window_size])
        score = SequenceMatcher(None, a, window).ratio()
        best_score = max(best_score, score)

        if score >= threshold:
            return True, score

    return False, best_score


# -----------------------------
# Citation Helpers
# -----------------------------

def extract_quoted_spans(response):
    """
    Extract quoted legal spans from citations like:
    [Law, Section 17 — "quoted provision"]
    """
    pattern = r'[—–-]\s*["\'](.+?)["\']\]'
    return re.findall(pattern, response, re.IGNORECASE)


BASIC_CITATION_PATTERN = re.compile(
    r'\[.*?(section|sec\.?|s)\s*:?\s*\w+.*?\]',
    re.IGNORECASE,
)

STRONG_CITATION_PATTERN = re.compile(
    r'\[.*?(section|sec\.?|s)\s*:?\s*\w+.*?[—–-].*?["\'].+?["\'].*?\]',
    re.IGNORECASE,
)


# -----------------------------
# Citation Quality Scoring
# -----------------------------

def score_citation_quality(response, retrieved_chunks=None):
    scores = {}

    basic_citation = bool(BASIC_CITATION_PATTERN.search(response))
    strong_citation = bool(STRONG_CITATION_PATTERN.search(response))

    scores["has_citation"] = 1 if basic_citation else 0
    scores["paragraph_citation"] = 1 if strong_citation else 0

    if not basic_citation or not retrieved_chunks:
        scores["quote_verbatim"] = None if not basic_citation else 0
        scores["quote_match_score"] = 0.0
        return scores

    quoted_spans = extract_quoted_spans(response)

    if not quoted_spans:
        scores["quote_verbatim"] = 0
        scores["quote_match_score"] = 0.0
        return scores

    match_scores = []

    for quote in quoted_spans:
        best = 0.0
        for chunk in retrieved_chunks:
            matched, score = fuzzy_match(quote, chunk)
            best = max(best, score)
        match_scores.append(best)

    avg_score = round(sum(match_scores) / len(match_scores), 3) if match_scores else 0.0

    scores["quote_match_score"] = avg_score
    scores["quote_verbatim"] = 1 if avg_score >= 0.72 else 0

    return scores


# -----------------------------
# Flexible Law Matching
# -----------------------------

def law_match(expected_law, response):
    """
    Avoid harsh exact string matching.
    Accept partial/fuzzy law mentions.
    """
    if not expected_law:
        return None

    expected = normalize(expected_law)
    response = normalize(response)

    if expected in response:
        return 1

    # remove common stop words
    tokens = [t for t in expected.split() if t not in {"act", "ordinance", "law", "the"}]

    if not tokens:
        return 0

    matched = sum(1 for t in tokens if t in response)
    ratio = matched / len(tokens)

    return 1 if ratio >= 0.6 else 0


# -----------------------------
# Fact Coverage
# -----------------------------

def score_fact_coverage(expected_facts, response):
    if not expected_facts:
        return None

    found = 0

    for fact in expected_facts:
        matched, score = fuzzy_match(fact, response, threshold=0.65)
        if matched:
            found += 1

    return round(found / len(expected_facts), 2)


# -----------------------------
# Main Response Scoring
# -----------------------------

def score_response(response, eval_item, source_chunks=None):
    scores = {}
    r = normalize(response)

    REFUSAL_PHRASES = [
    # English
    "cannot help",
    "cannot provide",
    "not able to",
    "i cannot",
    "i am unable",
    "outside the scope",

    # Roman Urdu
    "main madad nahi kar sakta",
    "main jawab nahi de sakta",
    "yeh mere scope se bahar hai",
    "main provide nahi kar sakta",
    "main is mein help nahi kar sakta",

    # Urdu script
    "میں مدد نہیں کر سکتا",
    "میں جواب نہیں دے سکتا",
    "یہ میرے دائرہ کار سے باہر ہے",
    "میں فراہم نہیں کر سکتا"
    ]

    did_refuse = any(p in r for p in REFUSAL_PHRASES)
    should_refuse = eval_item.get("should_refuse", False)

    # -----------------------------
    # Refusal Metrics
    # -----------------------------
    if should_refuse:
        scores["refusal_recall"] = 1 if did_refuse else 0
        scores["refusal_precision"] = 1 if did_refuse else 0
        scores["false_negative"] = 0 if did_refuse else 1
        scores["false_positive"] = None
    else:
        scores["refusal_recall"] = None
        scores["refusal_precision"] = 0 if did_refuse else 1
        scores["false_positive"] = 1 if did_refuse else 0
        scores["false_negative"] = None

    # -----------------------------
    # Non-refusal answer quality
    # -----------------------------
    if not should_refuse:
        citation_scores = score_citation_quality(response, source_chunks)
        scores.update(citation_scores)

        scores["correct_law"] = law_match(
            eval_item.get("expected_law"),
            response,
        )

        scores["fact_coverage"] = score_fact_coverage(
            eval_item.get("expected_facts", []),
            response,
        )
    else:
        scores["has_citation"] = None
        scores["paragraph_citation"] = None
        scores["quote_verbatim"] = None
        scores["quote_match_score"] = None
        scores["correct_law"] = None
        scores["fact_coverage"] = None

    # -----------------------------
    # Comprehension Pass
    # -----------------------------
    if should_refuse:
        scores["comprehension_pass"] = 1 if did_refuse else 0
    else:
        fact_ok = (
            scores["fact_coverage"] is None
            or scores["fact_coverage"] >= 0.5
        )

        law_ok = (
            scores["correct_law"] is None
            or scores["correct_law"] == 1
        )

        citation_ok = scores.get("has_citation", 0) == 1

        scores["comprehension_pass"] = 1 if (fact_ok and law_ok and citation_ok) else 0

    # -----------------------------
    # Disclaimer Presence
    # -----------------------------
    disclaimer_markers = [
        "note:",
        "disclaimer",
        "نوٹ:",
        "yeh general qanooni",
        "legal advice nahi",
        "not legal advice",
    ]

    scores["disclaimer_present"] = 1 if any(m in r for m in disclaimer_markers) else 0

    # -----------------------------
    # Overall Score
    # -----------------------------
    numeric = [
        v for v in scores.values()
        if isinstance(v, (int, float)) and v is not None
    ]

    scores["overall"] = round(sum(numeric) / len(numeric), 2) if numeric else 0

    return scores


# -----------------------------
# Evaluation Runner
# -----------------------------

def run_eval(ask_fn):
    with open("eval_set.json", "r", encoding="utf-8") as f:
        eval_set = json.load(f)

    results = []

    refusal_tp = refusal_fp = refusal_fn = refusal_tn = 0
    comprehension_passes = 0
    disclaimer_count = 0
    citation_count = 0
    citation_eligible = 0
    verbatim_count = 0
    verbatim_eligible = 0

    for item in eval_set:
        print(f"[{item['id']}] {item['question'][:70]}...")

        response, source_chunks = ask_fn(
            item["question"],
            province=item.get("province"),
            return_sources=True,
        )

        scores = score_response(response, item, source_chunks)

        if not item.get("should_refuse", False):
            citation_eligible += 1
            if scores.get("has_citation") == 1:
                citation_count += 1

            verbatim_eligible += 1
            if scores.get("quote_verbatim") == 1:
                verbatim_count += 1

        if item.get("should_refuse", False):
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
            "category": item.get("category"),
            "question": item["question"],
            "response": response[:500],
            "scores": scores,
        })

        print(
            f"  Pass={scores['comprehension_pass']} | "
            f"Citation={scores.get('has_citation')} | "
            f"Paragraph={scores.get('paragraph_citation')} | "
            f"Verbatim={scores.get('quote_verbatim')} "
            f"({scores.get('quote_match_score')}) | "
            f"Disclaimer={scores['disclaimer_present']} | "
            f"Overall={scores['overall']}"
        )

    total = len(eval_set)

    precision = (
        refusal_tp / (refusal_tp + refusal_fp)
        if (refusal_tp + refusal_fp) else 0
    )

    recall = (
        refusal_tp / (refusal_tp + refusal_fn)
        if (refusal_tp + refusal_fn) else 0
    )

    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall) else 0
    )

    print(f"""
==============================
EVALUATION RESULTS ({total})
==============================

REFUSAL METRICS
Precision : {precision:.0%}
Recall    : {recall:.0%}
F1        : {f1:.0%}
TP={refusal_tp} FP={refusal_fp} FN={refusal_fn} TN={refusal_tn}

COMPREHENSION
Pass Rate : {comprehension_passes / total:.0%} ({comprehension_passes}/{total})

CITATION QUALITY
Has Citation    : {citation_count}/{citation_eligible}
Verbatim Quotes : {verbatim_count}/{verbatim_eligible}
(Fuzzy threshold = 0.72)

DISCLAIMER
Present : {disclaimer_count / total:.0%} ({disclaimer_count}/{total})
""")

    with open("eval_results3.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Saved to eval_results3.json")


if __name__ == "__main__":
    from chatbot import ask
    run_eval(ask)
