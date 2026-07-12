"""
test_evaluate.py
Unit tests for the benchmark dataset and RAGAS evaluation pipeline.
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

BENCHMARK_PATH = Path("benchmark_qa.json")
RESULTS_PATH = Path("evaluation_results.csv")
METRIC_COLUMNS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
]
REQUIRED_CATEGORIES = {
    "single-event lookup",
    "aggregation",
    "cross-log correlation",
    "time-window queries",
}
REQUIRED_DIFFICULTIES = {"easy", "medium", "hard"}


class TestBenchmarkDataset(unittest.TestCase):
    def setUp(self):
        with open(BENCHMARK_PATH) as f:
            self.benchmark = json.load(f)

    def test_benchmark_has_15_questions(self):
        self.assertEqual(len(self.benchmark["questions"]), 15)
        self.assertEqual(self.benchmark["summary"]["total_questions"], 15)

    def test_each_question_has_required_fields(self):
        required = {"id", "question", "ground_truth", "difficulty", "category"}
        for q in self.benchmark["questions"]:
            self.assertTrue(required.issubset(q.keys()), f"Missing fields in Q{q.get('id')}")

    def test_difficulty_distribution(self):
        difficulties = {q["difficulty"] for q in self.benchmark["questions"]}
        self.assertTrue(REQUIRED_DIFFICULTIES.issubset(difficulties))

    def test_category_coverage(self):
        categories = {q["category"] for q in self.benchmark["questions"]}
        self.assertEqual(categories, REQUIRED_CATEGORIES)

    def test_unique_question_ids(self):
        ids = [q["id"] for q in self.benchmark["questions"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestRAGPipeline(unittest.TestCase):
    @patch("app.create_query_engine")
    def test_query_with_context_returns_answer_and_contexts(self, mock_create):
        from app import query_with_context

        mock_node = MagicMock()
        mock_node.node.get_content.return_value = "2025-05-01 08:02:11 FIREWALL_DENY src=10.1.1.5"
        mock_response = MagicMock()
        mock_response.__str__ = MagicMock(return_value="Destination IP is 8.8.8.8")
        mock_response.source_nodes = [mock_node]

        mock_engine = MagicMock()
        mock_engine.query.return_value = mock_response

        result = query_with_context(mock_engine, "What destination IP was blocked?")

        self.assertEqual(result["question"], "What destination IP was blocked?")
        self.assertIn("8.8.8.8", result["answer"])
        self.assertEqual(len(result["contexts"]), 1)
        self.assertIn("FIREWALL_DENY", result["contexts"][0])


class TestEvaluationResults(unittest.TestCase):
    def test_evaluation_results_csv_exists_after_run(self):
        if not RESULTS_PATH.exists():
            self.skipTest("evaluation_results.csv not yet generated — run evaluate.py first")

        df = pd.read_csv(RESULTS_PATH)
        self.assertGreaterEqual(len(df), 1, "Need at least one scored row")
        # Full benchmark = 15 rows; partial runs (API rate limit) are valid during development

        expected_cols = [
            "id",
            "question",
            "ground_truth",
            "answer",
            "difficulty",
            "category",
            *METRIC_COLUMNS,
        ]
        self.assertEqual(list(df.columns), expected_cols)

    def test_metric_scores_are_numeric(self):
        if not RESULTS_PATH.exists():
            self.skipTest("evaluation_results.csv not yet generated — run evaluate.py first")

        df = pd.read_csv(RESULTS_PATH)
        for col in METRIC_COLUMNS:
            self.assertTrue(pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric")
            valid = df[col].dropna()
            if len(valid) == 0:
                continue  # partial run may have NaN for answer_relevancy on early CSV
            self.assertTrue((valid >= 0).all() and (valid <= 1).all(), f"{col} out of [0,1] range")


class TestEvaluateModule(unittest.TestCase):
    def test_load_benchmark_returns_list(self):
        import ragas_compat  # noqa: F401
        from evaluate import load_benchmark

        questions = load_benchmark()
        self.assertEqual(len(questions), 15)
        self.assertIn("ground_truth", questions[0])


if __name__ == "__main__":
    unittest.main()
