"""
Main evaluation runner.

Usage:
  python run_eval.py                          # run all models, all tests
  python run_eval.py --models rag groq        # specific models
  python run_eval.py --category correctness   # specific category
  python run_eval.py --output results.json    # custom output file
  python run_eval.py --skip-rag               # skip your RAG (if server not running)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from test_cases import TEST_CASES
from models import get_models, RAGModel, GroqModel, GeminiModel
from evaluator import evaluate_response

# ── Rate limiting ─────────────────────────────────────────────────────────────
INTER_REQUEST_DELAY = 4.0   # seconds between API calls — Groq free tier is ~30 RPM
INTER_MODEL_DELAY   = 5.0


def run_evaluation(
    models,
    test_cases: List[dict],
    output_path: str = "eval_results.json",
    verbose: bool = True,
) -> dict:
    results = {
        "run_at": datetime.utcnow().isoformat() + "Z",
        "models": {},
    }

    total = len(models) * len(test_cases)
    done = 0

    for model in models:
        model_name = model.name
        if verbose:
            print(f"\n{'='*60}")
            print(f"Evaluating: {model_name}")
            print(f"{'='*60}")

        model_results = {
            "scores_by_test": [],
            "category_scores": {},
            "raw_responses": [],
        }

        category_buckets: dict = {}

        for tc in test_cases:
            done += 1
            tid = tc["id"]
            category = tc["category"]
            query = tc["query"]
            province = tc.get("province")

            if verbose:
                print(f"\n  [{done}/{total}] {tid} ({category})")
                print(f"  Q: {query[:80]}{'...' if len(query) > 80 else ''}")

            # Query the model
            t0 = time.time()
            response = model.query(query, province)
            latency = round(time.time() - t0, 2)

            if verbose:
                r_preview = response[:120].replace("\n", " ")
                print(f"  A: {r_preview}{'...' if len(response) > 120 else ''}")

            # Evaluate
            eval_result = evaluate_response(query, response, tc)
            score = eval_result.get("score", 0.5)

            if verbose:
                print(f"  Score: {score:.2f} | {eval_result.get('reasoning', '')[:80]}")

            # Accumulate
            category_buckets.setdefault(category, []).append(score)

            model_results["scores_by_test"].append({
                "test_id": tid,
                "category": category,
                "score": score,
                "latency_s": latency,
                "eval_method": eval_result.get("method"),
                "reasoning": eval_result.get("reasoning", ""),
            })
            model_results["raw_responses"].append({
                "test_id": tid,
                "query": query,
                "response": response,
            })

            time.sleep(INTER_REQUEST_DELAY)

        # Aggregate per category
        for cat, scores in category_buckets.items():
            model_results["category_scores"][cat] = {
                "mean": round(sum(scores) / len(scores), 3),
                "n": len(scores),
                "scores": scores,
            }

        # Overall mean
        all_scores = [s["score"] for s in model_results["scores_by_test"]]
        model_results["overall_mean"] = round(sum(all_scores) / len(all_scores), 3)

        results["models"][model_name] = model_results

        if verbose:
            print(f"\n  ── Summary for {model_name} ──")
            for cat, data in model_results["category_scores"].items():
                print(f"     {cat:20s}: {data['mean']:.2f}  (n={data['n']})")
            print(f"     {'OVERALL':20s}: {model_results['overall_mean']:.2f}")

        time.sleep(INTER_MODEL_DELAY)

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"\n✓ Results saved to: {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate Pakistan Labour RAG")
    parser.add_argument("--output", default="eval_results.json")
    parser.add_argument("--category", default=None,
                        help="Filter to one category: correctness|hallucination|unsafe_advice|over_refusal")
    parser.add_argument("--skip-rag", action="store_true",
                        help="Skip the RAG model (use when FastAPI server is not running)")
    parser.add_argument("--quick", action="store_true",
                        help="Run only 2 tests per category (faster)")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()

    # Filter test cases
    test_cases = TEST_CASES
    if args.category:
        test_cases = [tc for tc in test_cases if tc["category"] == args.category]
        if not test_cases:
            print(f"No test cases for category: {args.category}")
            sys.exit(1)

    if args.quick:
        # Keep 2 per category
        seen: dict = {}
        filtered = []
        for tc in test_cases:
            cat = tc["category"]
            if seen.get(cat, 0) < 2:
                filtered.append(tc)
                seen[cat] = seen.get(cat, 0) + 1
        test_cases = filtered

    # Build models
    all_models = get_models()
    if args.skip_rag:
        all_models = [m for m in all_models if not isinstance(m, RAGModel)]

    if not all_models:
        print("No models to evaluate. Check API keys and --skip-rag flag.")
        sys.exit(1)

    print(f"\nEvaluation plan:")
    print(f"  Models     : {[m.name for m in all_models]}")
    print(f"  Test cases : {len(test_cases)}")
    print(f"  Output     : {args.output}")

    results = run_evaluation(
        models=all_models,
        test_cases=test_cases,
        output_path=args.output,
        verbose=args.verbose,
    )

    # Print final leaderboard
    print("\n" + "=" * 60)
    print("LEADERBOARD")
    print("=" * 60)
    sorted_models = sorted(
        results["models"].items(),
        key=lambda x: x[1]["overall_mean"],
        reverse=True,
    )
    header = f"{'Model':<35} {'Overall':>8}"
    cats = ["correctness", "hallucination", "unsafe_advice", "over_refusal"]
    for cat in cats:
        header += f"  {cat[:10]:>10}"
    print(header)
    print("-" * len(header))
    for model_name, data in sorted_models:
        row = f"{model_name:<35} {data['overall_mean']:>8.2f}"
        for cat in cats:
            score = data["category_scores"].get(cat, {}).get("mean", float("nan"))
            row += f"  {score:>10.2f}"
        print(row)


if __name__ == "__main__":
    main()