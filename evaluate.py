"""
evaluate.py
Run all benchmark questions through the RAG pipeline, score them with RAGAS,
and save per-question metric results to evaluation_results.csv.

Metrics computed:
  - faithfulness       – answer contains only information from retrieved context
  - answer_relevancy   – answer is relevant to the question
  - context_precision  – retrieved chunks are ranked with relevant ones first
  - context_recall     – retrieval found all chunks needed to answer the question
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import ragas_compat  # noqa: F401 — patch imports before ragas loads

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings as LangchainOpenAIEmbeddings
from openai import OpenAI
from ragas import evaluate
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from ragas.llms import llm_factory
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.run_config import RunConfig

from app import create_query_engine, query_with_context

BENCHMARK_PATH = Path("benchmark_qa.json")
RESULTS_PATH = Path("evaluation_results.csv")
RAG_CACHE_PATH = Path("rag_responses.json")
PROJECT_VENV = Path(__file__).resolve().parent / "venv"

METRIC_COLUMNS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
]


def ensure_project_venv() -> None:
    """Warn when a different virtual environment is active."""
    if not PROJECT_VENV.exists():
        return
    if Path(sys.prefix).resolve() != PROJECT_VENV.resolve():
        warnings.warn(
            f"Active Python is not the project venv ({PROJECT_VENV}). "
            f"Use: {PROJECT_VENV}/bin/python evaluate.py ...",
            stacklevel=2,
        )


def load_benchmark(path: Path = BENCHMARK_PATH) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["questions"]


def create_ragas_clients(max_workers: int = 2):
    """Create RAGAS LLM and embedding clients using the GitHub/Azure endpoint."""
    load_dotenv()
    api_key = os.getenv("GITHUB_TOKEN")
    base_url = "https://models.inference.ai.azure.com/"

    if not api_key:
        raise ValueError("GITHUB_TOKEN is not set")

    llm_client = OpenAI(api_key=api_key, base_url=base_url)

    # answer_relevancy requires embed_query/embed_documents (LangChain interface).
    langchain_embeddings = LangchainOpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
        base_url=base_url,
    )
    embeddings = LangchainEmbeddingsWrapper(langchain_embeddings)

    # Wrap LLM client into llm factory
    llm = llm_factory("gpt-4o-mini", client=llm_client)

    # Configuration for RAGAS
    # max_workers: how many concurrent threads are used for parallel tasks
    # max_retries: how many times the system should attempt to call the API
    # max_wait: maximum time the system should wait between retries or for an API response before marking the task as failed.
    run_config = RunConfig(max_workers=max_workers, max_retries=5, max_wait=120)
    return llm, embeddings, run_config


def collect_rag_responses(
    questions: list[dict],
    top_k: int = 3,
    cache_path: Path | None = RAG_CACHE_PATH,
    use_cache: bool = False,
) -> list[dict]:
    """Run each benchmark question through the RAG pipeline."""
    if use_cache and cache_path and cache_path.exists():
        with open(cache_path) as f:
            cached = json.load(f)
        requested_ids = {q["id"] for q in questions}
        records = [r for r in cached if r["id"] in requested_ids]
        id_order = {q["id"]: i for i, q in enumerate(questions)}
        records.sort(key=lambda r: id_order[r["id"]])
        if len(records) != len(questions):
            missing = requested_ids - {r["id"] for r in records}
            raise ValueError(
                f"Cache {cache_path} is missing responses for question ids: {sorted(missing)}"
            )
        print(f"Loaded {len(records)} cached RAG responses from {cache_path}")
        return records

    query_engine = create_query_engine(top_k=top_k)
    records = []

    # Enumerate over questions and ask questions to LLM
    # Append results to records includes answer and contexts
    for i, item in enumerate(questions, start=1):
        print(f"  [{i}/{len(questions)}] RAG query: {item['question'][:70]}...")
        rag_out = query_with_context(query_engine, item["question"])
        records.append(
            {
                "id": item["id"],
                "question": item["question"],
                "ground_truth": item["ground_truth"],
                "difficulty": item["difficulty"],
                "category": item["category"],
                "answer": rag_out["answer"],
                "contexts": rag_out["contexts"],
            }
        )

    if cache_path:
        with open(cache_path, "w") as f:
            json.dump(records, f, indent=2)
        print(f"Saved RAG responses to {cache_path}")

    return records


def run_ragas_evaluation(records: list[dict], ragas_llm, ragas_embeddings, ragas_run_config: RunConfig):
    """Score collected RAG outputs with all four RAGAS metrics."""
    # Convert a list of dicts to a `pyarrow.Table` to create a [`Dataset`]`
    dataset = Dataset.from_list(
        [
            {
                "question": r["question"],
                "ground_truth": r["ground_truth"],
                "answer": r["answer"],
                "contexts": r["contexts"],
            }
            for r in records
        ]
    )

    print(f"\nRunning RAGAS evaluation on {len(records)} samples...")
    print(f"  max_workers={ragas_run_config.max_workers} (lower = fewer parallel API calls)")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        run_config=ragas_run_config,
        raise_exceptions=False,
    )
    return result


def save_results(records: list[dict], ragas_result, output_path: Path = RESULTS_PATH) -> pd.DataFrame:
    """Merge RAG outputs with RAGAS scores and write evaluation_results.csv."""
    scores_df = pd.DataFrame(ragas_result.scores)
    meta_df = pd.DataFrame(records)

    df = pd.concat(
        [
            meta_df[["id", "question", "ground_truth", "answer", "difficulty", "category"]],
            scores_df[METRIC_COLUMNS],
        ],
        axis=1,
    )

    df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path} ({len(df)} rows)")
    print("\nMetric summary (mean, non-NaN):")
    for col in METRIC_COLUMNS:
        valid = df[col].dropna()
        if len(valid):
            print(f"  {col}: {valid.mean():.4f}  ({len(valid)}/{len(df)} scored)")
        else:
            print(f"  {col}: no valid scores")

    return df


def main() -> None:
    ensure_project_venv()

    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on benchmark QA pairs")
    parser.add_argument("--top-k", type=int, default=3, help="Retrieval depth (default: 3)")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only first N questions")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Reuse cached RAG responses from rag_responses.json",
    )
    parser.add_argument(
        "--ragas-only",
        action="store_true",
        help="Skip RAG queries; score cached responses with RAGAS only",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="RAGAS parallel workers (default: 2; use 1 to reduce rate-limit risk)",
    )
    parser.add_argument("--output", type=str, default=str(RESULTS_PATH), help="Output CSV path")
    args = parser.parse_args()

    if args.ragas_only:
        args.use_cache = True

    questions = load_benchmark()
    if args.limit:
        questions = questions[: args.limit]
        print(f"Evaluating first {len(questions)} question(s) (--limit {args.limit})")
    else:
        print(f"Evaluating all {len(questions)} benchmark questions")

    if args.ragas_only:
        print("\nStep 1: Skipped (--ragas-only); loading cached RAG responses...")
    else:
        print("\nStep 1: Collecting RAG pipeline responses...")

    # This is the RAG pipeline
    records = collect_rag_responses(
        questions,
        top_k=args.top_k,
        use_cache=args.use_cache,
    )

    print("\nStep 2: Scoring with RAGAS...")
    ragas_llm, ragas_embeddings, ragas_run_config = create_ragas_clients(max_workers=args.max_workers)
    ragas_result = run_ragas_evaluation(records, ragas_llm, ragas_embeddings, ragas_run_config)

    print("\nStep 3: Saving results...")
    save_results(records, ragas_result, Path(args.output))


if __name__ == "__main__":
    main()
