# Failure Analysis (on RAGAS Score)

Goal is to diagnose why some questions perform poorly, quantify metric distributions, and test whether retrieval depth (top_k) significantly affects faithfulness

## failure_analysis.py
- Computes summary statistics for each metric.
- Identifies the worst‑performing questions (bottom 20% by faithfulness)
- Attaches manual failure annotations (from a pre‑defined dictionary) to those failures for qualitative review.
- If a separate top_k_comparison.csv exists, performs a statistical t‑test to see if changing the number of retrieved chunks significantly affects faithfulness.
- Generates a histogram and category‑based boxplot to visualise score distributions.
- Saves all outputs (annotations, summary CSV, charts) for later inspection.

## Plot distributions of [faithfulness scores](https://code-with-amitk.github.io/Machine%20Learning/RAGAS/Introduction.html) using matplotlib/seaborn
- Check are failures clustered around certain query types?

```
    df = load_results("evaluation_results.csv")

```