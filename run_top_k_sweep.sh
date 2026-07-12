#!/usr/bin/env bash
# Phase 4.4 — Compare RAGAS scores at top_k = 1, 3, 5, 10
# WARNING: Each value re-runs RAG + RAGAS and consumes many API calls.
# Only run after the GitHub Models daily limit (150/day) has reset.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/venv/bin/python"
OUT="$ROOT/top_k_comparison.csv"

echo "top_k,faithfulness_mean,answer_relevancy_mean,context_precision_mean,context_recall_mean,n_questions" > "$OUT"

for K in 1 3 5 10; do
  echo "=== top_k=$K ==="
  TMP="$ROOT/evaluation_results_topk_${K}.csv"
  "$PYTHON" "$ROOT/evaluate.py" --top-k "$K" --max-workers 1 --output "$TMP"
  "$PYTHON" - <<PY
import pandas as pd
df = pd.read_csv("$TMP")
metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
means = {m: df[m].dropna().mean() for m in metrics}
row = f"$K,{means['faithfulness']},{means['answer_relevancy']},{means['context_precision']},{means['context_recall']},{len(df)}"
with open("$OUT", "a") as f:
    f.write(row + "\\n")
print("Appended:", row)
PY
done

echo "Done. Comparison table: $OUT"
echo "Re-run: python failure_analysis.py"
