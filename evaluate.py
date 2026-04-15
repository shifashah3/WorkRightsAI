import json
import re
from chatbot import ask 

def score_response(response, eval_item):
    scores = {}
    
    # 1. Citation present (does it have the [Law, Section — "quote"] format)
    citation_pattern = r"\[[^\]]*(Section|سیکشن)\s*\d+[^\]]*\]"
    has_citation = bool(re.search(citation_pattern, response))
    scores["has_citation"] = 1 if has_citation else 0
    
    # 2. Correct law cited
    if eval_item["expected_law"]:
        law_cited = eval_item["expected_law"].lower() in response.lower()
        scores["correct_law"] = 1 if law_cited else 0
    else:
        scores["correct_law"] = None
    
    # 3. Expected facts present
    facts_found = 0
    for fact in eval_item["expected_facts"]:
        if fact.lower() in response.lower():
            facts_found += 1
    fact_score = facts_found / len(eval_item["expected_facts"]) if eval_item["expected_facts"] else None
    scores["fact_coverage"] = round(fact_score, 2) if fact_score is not None else None
    
    # 4. Refusal quality
    if eval_item["should_refuse"]:
        refused = any(phrase in response.lower() for phrase in [
            "cannot provide", "not able to", "consult a lawyer",
            "not legal advice", "cannot help with", "not qualified to", "beyond the scope", "not in database", "i'm not able to help"
        ])
        scores["correct_refusal"] = 1 if refused else 0
    else:
        scores["correct_refusal"] = None
    
    # 5. Disclaimer present
    scores["has_disclaimer"] = 1 if "DISCLAIMER" in response or "disclaimer" in response else 0
    
    # Overall score (average of non-None scores)
    numeric = [v for v in scores.values() if v is not None]
    scores["overall"] = round(sum(numeric) / len(numeric), 2) if numeric else 0
    
    return scores


def run_eval():
    with open("eval_set.json", "r", encoding="utf-8") as f:
        eval_set = json.load(f)
    
    results = []
    for item in eval_set:
        print(f"Running {item['id']}: {item['question'][:60]}...")
        response = ask(item["question"], province=item.get("province"))
        scores = score_response(response, item)  # now response is a string
        
        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "response": response,
            "scores": scores
        })
        
        print(f"  Overall: {scores['overall']} | Citation: {scores['has_citation']} | Facts: {scores['fact_coverage']}")
    
    # # Summary
    # overall_scores = [r["scores"]["overall"] for r in results]
    # print(f"\n=== EVAL SUMMARY ===")
    # print(f"Mean score: {sum(overall_scores)/len(overall_scores):.2f}")
    # print(f"Citation rate: {sum(r['scores']['has_citation'] for r in results)/len(results):.0%}")
    
    by_category = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, []).append(r["scores"]["overall"])
    
    
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\nFull results saved to eval_results.json")

if __name__ == "__main__":
    run_eval()