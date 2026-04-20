"""
Plot evaluation results from eval_results.json.

Produces:
  1. Radar / spider chart — per-model across all 4 dimensions
  2. Grouped bar chart    — dimension breakdown per model
  3. Per-test heatmap     — raw scores, every test × model
  4. Latency box plot     — response time distribution per model

Usage:
  python plot_results.py                     # reads eval_results.json
  python plot_results.py --input my.json     # custom file
  python plot_results.py --output plots/     # custom output dir
"""

import argparse
import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ── Styling ───────────────────────────────────────────────────────────────────
DARK_BG    = "#0f1117"
CARD_BG    = "#1a1d27"
ACCENT     = "#4f8ef7"
CATEGORIES = ["correctness", "hallucination", "unsafe_advice", "over_refusal"]
CAT_LABELS = ["Correctness", "Hallucination\n(resistance)", "Safe Refusal\n(unsafe_advice)", "Low Over-\nRefusal"]

# Colour palette — one per model (supports up to 8)
PALETTE = [
    "#4f8ef7", "#f76b4f", "#4fc98e", "#f7c94f",
    "#b04ff7", "#f74f9e", "#4fd7f7", "#f7f74f",
]

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": "#2e3347",
    "axes.labelcolor": "#c8cfe0",
    "xtick.color": "#8890a8",
    "ytick.color": "#8890a8",
    "text.color": "#c8cfe0",
    "grid.color": "#2e3347",
    "grid.linewidth": 0.6,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
})


def load_results(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def model_names(results: dict):
    return list(results["models"].keys())


def shorten(name: str, max_len: int = 22) -> str:
    return name if len(name) <= max_len else name[:max_len - 1] + "…"


# ─── 1. Radar Chart ───────────────────────────────────────────────────────────

def plot_radar(results: dict, out_dir: Path):
    models = model_names(results)
    num_cats = len(CATEGORIES)
    angles = np.linspace(0, 2 * np.pi, num_cats, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True),
                           facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(CAT_LABELS, size=9, color="#c8cfe0")
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.50", "0.75", "1.0"], size=7, color="#8890a8")
    ax.yaxis.grid(True, color="#2e3347", linewidth=0.8)
    ax.xaxis.grid(True, color="#2e3347", linewidth=0.8)
    ax.spines["polar"].set_color("#2e3347")

    patches = []
    for i, model in enumerate(models):
        color = PALETTE[i % len(PALETTE)]
        cat_scores = results["models"][model]["category_scores"]
        values = [cat_scores.get(c, {}).get("mean", 0) for c in CATEGORIES]
        values += values[:1]

        ax.plot(angles, values, color=color, linewidth=2, linestyle="solid", zorder=3)
        ax.fill(angles, values, color=color, alpha=0.12, zorder=2)
        patches.append(mpatches.Patch(color=color, label=shorten(model)))

    ax.set_title("Model Comparison — Radar", color="#e0e6f0", pad=20, fontsize=14)
    ax.legend(handles=patches, loc="upper right", bbox_to_anchor=(1.35, 1.15),
              framealpha=0.3, edgecolor="#2e3347", fontsize=8)

    fig.tight_layout()
    path = out_dir / "1_radar_chart.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── 2. Grouped Bar Chart ────────────────────────────────────────────────────

def plot_grouped_bars(results: dict, out_dir: Path):
    models = model_names(results)
    n_models = len(models)
    n_cats = len(CATEGORIES)

    x = np.arange(n_cats)
    width = 0.8 / n_models

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)

    for i, model in enumerate(models):
        color = PALETTE[i % len(PALETTE)]
        cat_scores = results["models"][model]["category_scores"]
        scores = [cat_scores.get(c, {}).get("mean", 0) for c in CATEGORIES]

        bars = ax.bar(
            x + i * width - (n_models - 1) * width / 2,
            scores,
            width * 0.88,
            label=shorten(model),
            color=color,
            alpha=0.88,
            zorder=3,
        )
        for bar, score in zip(bars, scores):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.015,
                f"{score:.2f}",
                ha="center", va="bottom", fontsize=7, color=color,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(CAT_LABELS, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score (0–1)", fontsize=10)
    ax.set_title("Evaluation Scores by Dimension", fontsize=14)
    ax.yaxis.grid(True, zorder=0)
    ax.legend(fontsize=8, framealpha=0.3, edgecolor="#2e3347")

    fig.tight_layout()
    path = out_dir / "2_grouped_bars.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── 3. Per-test Heatmap ─────────────────────────────────────────────────────

def plot_heatmap(results: dict, out_dir: Path):
    models = model_names(results)

    # Collect all test IDs in order
    first_model_data = results["models"][models[0]]["scores_by_test"]
    test_ids = [t["test_id"] for t in first_model_data]
    test_cats = [t["category"] for t in first_model_data]

    # Build matrix: rows = models, cols = tests
    matrix = []
    for model in models:
        row = []
        score_map = {t["test_id"]: t["score"]
                     for t in results["models"][model]["scores_by_test"]}
        for tid in test_ids:
            row.append(score_map.get(tid, 0))
        matrix.append(row)

    matrix = np.array(matrix)

    cmap = LinearSegmentedColormap.from_list(
        "rg", ["#c0392b", "#f39c12", "#27ae60"], N=256
    )

    fig_width = max(10, len(test_ids) * 0.55)
    fig_height = max(4, len(models) * 0.6 + 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)

    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(len(test_ids)))
    ax.set_xticklabels(
        [f"{tid}\n({cat[:3]})" for tid, cat in zip(test_ids, test_cats)],
        rotation=0, ha="center", fontsize=7.5,
    )
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([shorten(m, 30) for m in models], fontsize=8)
    ax.set_title("Per-Test Score Heatmap  (green=1.0, red=0.0)", fontsize=13)

    # Cell annotations
    for r in range(len(models)):
        for c in range(len(test_ids)):
            val = matrix[r, c]
            ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                    fontsize=6.5, color="white" if val < 0.65 else "#111")

    cbar = fig.colorbar(im, ax=ax, fraction=0.015, pad=0.02)
    cbar.ax.tick_params(labelsize=7, colors="#8890a8")
    cbar.outline.set_edgecolor("#2e3347")

    fig.tight_layout()
    path = out_dir / "3_heatmap.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── 4. Latency Violin/Box Plot ──────────────────────────────────────────────

def plot_latency(results: dict, out_dir: Path):
    models = model_names(results)
    latencies = []
    valid_models = []

    for model in models:
        lats = [t["latency_s"] for t in results["models"][model]["scores_by_test"]
                if t.get("latency_s") is not None]
        if lats:
            latencies.append(lats)
            valid_models.append(model)

    if not latencies:
        print("  No latency data available — skipping.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)

    positions = range(1, len(valid_models) + 1)
    parts = ax.violinplot(latencies, positions=positions, showmedians=True,
                          showextrema=True)

    for i, (body, color) in enumerate(zip(parts["bodies"], PALETTE)):
        body.set_facecolor(color)
        body.set_alpha(0.6)
        body.set_edgecolor(color)

    parts["cmedians"].set_colors("#ffffff")
    parts["cmedians"].set_linewidth(2)
    parts["cbars"].set_colors("#8890a8")
    parts["cmaxes"].set_colors("#8890a8")
    parts["cmins"].set_colors("#8890a8")

    ax.set_xticks(positions)
    ax.set_xticklabels([shorten(m, 20) for m in valid_models], rotation=12, ha="right", fontsize=8)
    ax.set_ylabel("Response time (s)", fontsize=10)
    ax.set_title("Response Latency Distribution", fontsize=13)
    ax.yaxis.grid(True, zorder=0)

    fig.tight_layout()
    path = out_dir / "4_latency.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── 5. Overall Leaderboard Bar ──────────────────────────────────────────────

def plot_leaderboard(results: dict, out_dir: Path):
    models = model_names(results)
    overall = [results["models"][m]["overall_mean"] for m in models]
    sorted_pairs = sorted(zip(models, overall), key=lambda x: x[1], reverse=True)
    models_sorted, scores_sorted = zip(*sorted_pairs)

    fig, ax = plt.subplots(figsize=(8, max(3.5, len(models) * 0.7)), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)

    colors = [PALETTE[i % len(PALETTE)] for i in range(len(models_sorted))]
    bars = ax.barh(range(len(models_sorted)), scores_sorted,
                   color=colors, alpha=0.88, zorder=3, height=0.55)

    for i, (bar, score) in enumerate(zip(bars, scores_sorted)):
        ax.text(score + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{score:.3f}", va="center", fontsize=9,
                color=colors[i], fontweight="bold")

    ax.set_yticks(range(len(models_sorted)))
    ax.set_yticklabels([shorten(m, 28) for m in models_sorted], fontsize=9)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Overall Score (mean across all tests)", fontsize=10)
    ax.set_title("Overall Model Leaderboard", fontsize=14)
    ax.xaxis.grid(True, zorder=0)
    ax.invert_yaxis()

    fig.tight_layout()
    path = out_dir / "5_leaderboard.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── Runner ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="eval_results.json")
    parser.add_argument("--output", default="plots")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Results file not found: {args.input}")
        print("Run `python run_eval.py` first to generate results.")
        return

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(args.input)
    print(f"Loaded results for {len(results['models'])} models")
    print(f"Plotting to: {out_dir}/\n")

    plot_radar(results, out_dir)
    plot_grouped_bars(results, out_dir)
    plot_heatmap(results, out_dir)
    plot_latency(results, out_dir)
    plot_leaderboard(results, out_dir)

    print("\n✓ All plots saved.")


if __name__ == "__main__":
    main()