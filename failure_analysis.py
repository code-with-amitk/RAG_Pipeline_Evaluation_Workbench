"""
failure_analysis.py
Phase 4 — Failure mode and distribution analysis over RAGAS evaluation results.

Works with partial results when API rate limits prevent a full run.
Re-run evaluate.py when the daily limit resets to populate all benchmark rows, then re-run
this script for complete statistics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats

RESULTS_PATH = Path("evaluation_results.csv")
TOP_K_COMPARISON_PATH = Path("top_k_comparison.csv")
ANNOTATIONS_PATH = Path("failure_annotations.json")
CHARTS_DIR = Path("charts")

BENCHMARK_TOTAL = 15

METRIC_COLUMNS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
]

# Manual failure-mode annotations for the bottom 20% by faithfulness (Phase 4.3).
# Extend this list when more questions are scored.
DEFAULT_ANNOTATIONS = {
    1: {
        "failure_reason": "answer_relevancy missing (NaN) — RAGAS embedding interface error during partial run; faithfulness and context metrics scored 1.0.",
        "category": "single-event lookup",
        "difficulty": "easy",
    },
    2: {
        "failure_reason": "answer_relevancy missing (NaN) — same embedding issue; retrieval and faithfulness otherwise strong for this easy lookup question.",
        "category": "single-event lookup",
        "difficulty": "easy",
    },
}

# Reads the main evaluation_results.csv 
def load_results(path: Path = RESULTS_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run evaluate.py first (even with --limit 2)."
        )
    return pd.read_csv(path)

# For each metric column, drops NaN values
# Computes count, mean(Average), median(Middle), and
# standard deviation(how much individual data points deviate from the mean) of the valid scores.
def metric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Mean, median, std for each RAGAS metric (non-NaN values only)."""
    rows = []
    for col in METRIC_COLUMNS:
        valid = df[col].dropna()    # dropna() Drops the NaN rows from dataframe
        rows.append(
            {
                "metric": col,
                "count": len(valid),
                "mean": valid.mean() if len(valid) else float("nan"),
                "median": valid.median() if len(valid) else float("nan"),
                "std": valid.std() if len(valid) > 1 else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def bottom_faithfulness_slice(df: pd.DataFrame, fraction: float = 0.2) -> pd.DataFrame:
    """Return the bottom fraction of rows by faithfulness score."""
    scored = df.dropna(subset=["faithfulness"]).sort_values("faithfulness")
    if scored.empty:
        return scored
    n = max(1, int(len(scored) * fraction))
    return scored.head(n)


def build_failure_annotations(df: pd.DataFrame) -> list[dict]:
    """Identify bottom 20% by faithfulness and attach manual failure annotations."""
    bottom = bottom_faithfulness_slice(df, fraction=0.2)
    annotations = []
    for _, row in bottom.iterrows():
        qid = int(row["id"])
        preset = DEFAULT_ANNOTATIONS.get(qid, {})
        annotations.append(
            {
                "id": qid,
                "question": row["question"],
                "faithfulness": row["faithfulness"],
                "answer_relevancy": row.get("answer_relevancy"),
                "category": row.get("category", preset.get("category")),
                "difficulty": row.get("difficulty", preset.get("difficulty")),
                "failure_reason": preset.get(
                    "failure_reason",
                    "Review manually — low faithfulness relative to other scored questions.",
                ),
            }
        )
    return annotations


def save_annotations(annotations: list[dict], path: Path = ANNOTATIONS_PATH) -> None:
    with open(path, "w") as f:
        json.dump(annotations, f, indent=2)
    print(f"Saved {len(annotations)} failure annotation(s) to {path}")


def load_top_k_comparison(path: Path = TOP_K_COMPARISON_PATH) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def top_k_significance_test(comparison: pd.DataFrame) -> dict:
    """
    Basic t-test: compare mean faithfulness between lowest and highest top_k
    in the comparison table (requires per-question rows or pre-aggregated means).
    """
    if comparison is None or len(comparison) < 2:
        return {"status": "skipped", "reason": "Need top_k_comparison.csv with at least 2 top_k values"}

    if "faithfulness" in comparison.columns and "top_k" in comparison.columns:
        # Per-question format: faithfulness column per row with top_k label
        groups = comparison.groupby("top_k")["faithfulness"].apply(list)
        if len(groups) < 2:
            return {"status": "skipped", "reason": "Need at least 2 distinct top_k groups"}
        low_k = groups.index.min()
        high_k = groups.index.max()
        a = groups[low_k]
        b = groups[high_k]
    elif "faithfulness_mean" in comparison.columns:
        # Aggregated format — not enough points for a real t-test; use means only
        return {
            "status": "insufficient_data",
            "reason": "Aggregated means only — re-run with per-question top_k sweep for t-test",
            "comparison": comparison[["top_k", "faithfulness_mean"]].to_dict("records"),
        }
    else:
        return {"status": "skipped", "reason": "Unrecognized top_k_comparison.csv format"}

    if len(a) < 2 or len(b) < 2:
        return {
            "status": "insufficient_data",
            "reason": f"Need ≥2 scored questions per top_k (have {len(a)} vs {len(b)})",
        }

    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
    return {
        "status": "ok",
        "low_top_k": int(low_k),
        "high_top_k": int(high_k),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "significant_at_0.05": bool(p_value < 0.05),
    }


def plot_faithfulness_histogram(df: pd.DataFrame, output_dir: Path = CHARTS_DIR) -> Path:
    output_dir.mkdir(exist_ok=True)
    scored = df.dropna(subset=["faithfulness"])
    if scored.empty:
        raise ValueError("No faithfulness scores to plot")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    sns.histplot(scored["faithfulness"], bins=max(2, len(scored)), kde=len(scored) > 2, ax=axes[0])
    axes[0].set_title("Faithfulness Score Distribution")
    axes[0].set_xlabel("Faithfulness")
    axes[0].set_ylabel("Count")
    axes[0].set_xlim(0, 1.05)

    if "category" in scored.columns and scored["category"].nunique() > 0:
        sns.boxplot(data=scored, x="category", y="faithfulness", ax=axes[1])
        axes[1].set_title("Faithfulness by Question Category")
        axes[1].set_xlabel("Category")
        axes[1].tick_params(axis="x", rotation=25)
    else:
        axes[1].set_visible(False)

    fig.tight_layout()
    out = output_dir / "faithfulness_distribution.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


def print_report(df: pd.DataFrame, summary: pd.DataFrame, ttest: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  Phase 4 — Failure Mode Analysis")
    print(f"{'='*60}")
    print(f"  Scored questions: {len(df)} / {BENCHMARK_TOTAL} benchmark total")
    if len(df) < BENCHMARK_TOTAL:
        print("  NOTE: Partial dataset — GitHub Models daily limit (150 calls/day)")
        print("        blocked full RAGAS run. Re-run evaluate.py when limit resets.")

    print(f"\n--- Metric summary (mean / median / std) ---")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    print(f"\n--- t-test (top_k faithfulness) ---")
    for key, val in ttest.items():
        print(f"  {key}: {val}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 failure mode analysis")
    parser.add_argument("--input", type=str, default=str(RESULTS_PATH))
    parser.add_argument("--no-plots", action="store_true", help="Skip chart generation")
    args = parser.parse_args()

    df = load_results(Path(args.input))
    print("df\n",df.head())
    summary = metric_summary(df)
    print("summary:", summary.head())
    annotations = build_failure_annotations(df)
    print("annotation:", annotations.head())
    save_annotations(annotations)

    comparison = load_top_k_comparison()
    ttest = top_k_significance_test(comparison)

    print_report(df, summary, ttest)

    if not args.no_plots:
        chart_path = plot_faithfulness_histogram(df)
        print(f"\nChart saved: {chart_path}")

    summary.to_csv("metric_summary.csv", index=False)
    print("Metric summary saved: metric_summary.csv")


if __name__ == "__main__":
    main()
