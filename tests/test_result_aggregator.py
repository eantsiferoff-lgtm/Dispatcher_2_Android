import unittest

from core.models import Result
from core.result_aggregator import ResultAggregator


class TestResultAggregator(unittest.TestCase):
    def test_single_result_contract(self):
        result = Result(
            task_id="TASK-000001",
            status="completed",
            text="Готово",
            artifacts=["report.pdf"],
            sources=["source-1"],
            warnings=["warning-1"],
        )

        normalized = ResultAggregator().normalize("test-skill", result)

        self.assertEqual(normalized["skill"], "test-skill")
        self.assertEqual(normalized["status"], "completed")
        self.assertEqual(normalized["data"], "Готово")
        self.assertEqual(
            normalized["metadata"]["artifacts"],
            ["report.pdf"],
        )

    def test_multiple_results_preserve_order(self):
        aggregator = ResultAggregator()

        results = [
            aggregator.normalize(
                "skill-a",
                Result(
                    task_id="TASK-000001",
                    status="completed",
                    text="A",
                ),
            ),
            aggregator.normalize(
                "skill-b",
                Result(
                    task_id="TASK-000001",
                    status="completed",
                    text="B",
                ),
            ),
            aggregator.normalize(
                "skill-c",
                Result(
                    task_id="TASK-000001",
                    status="completed",
                    text="C",
                ),
            ),
        ]

        self.assertEqual(
            [item["skill"] for item in results],
            ["skill-a", "skill-b", "skill-c"],
        )
        self.assertEqual(
            [item["data"] for item in results],
            ["A", "B", "C"],
        )
        self.assertEqual(len(results), 3)

    def test_aggregate_multiple_results(self):
        aggregator = ResultAggregator()

        results = [
            aggregator.normalize(
                "skill-a",
                Result(task_id="TASK-000001", status="completed", text="A"),
            ),
            aggregator.normalize(
                "skill-b",
                Result(task_id="TASK-000001", status="completed", text="B"),
            ),
        ]

        aggregated = aggregator.aggregate(results)

        self.assertEqual(aggregated["status"], "completed")
        self.assertEqual(aggregated["results"], results)
        self.assertEqual(aggregated["data"], ["A", "B"])

    def test_aggregate_failed_result(self):
        aggregator = ResultAggregator()

        results = [
            aggregator.normalize(
                "skill-a",
                Result(task_id="TASK-000001", status="completed", text="A"),
            ),
            aggregator.normalize(
                "skill-b",
                Result(task_id="TASK-000001", status="failed", text=""),
            ),
        ]

        aggregated = aggregator.aggregate(results)

        self.assertEqual(aggregated["status"], "partial_success")
        self.assertEqual(aggregated["results"], results)

    def test_aggregate_partial_result(self):
        aggregator = ResultAggregator()

        result = aggregator.normalize(
            "skill-a",
            Result(
                task_id="TASK-000001",
                status="partial_success",
                text="partial",
            ),
        )

        aggregated = aggregator.aggregate([result])

        self.assertEqual(aggregated["status"], "partial_success")
        self.assertEqual(aggregated["data"], ["partial"])

    def test_aggregate_empty_results(self):
        aggregator = ResultAggregator()

        aggregated = aggregator.aggregate([])

        self.assertEqual(aggregated["status"], "empty")
        self.assertEqual(aggregated["data"], [])
        self.assertEqual(aggregated["results"], [])

    def test_aggregate_preserves_individual_results(self):
        aggregator = ResultAggregator()

        first = aggregator.normalize(
            "skill-a",
            Result(task_id="TASK-000001", status="completed", text="A"),
        )
        second = aggregator.normalize(
            "skill-b",
            Result(task_id="TASK-000001", status="completed", text="B"),
        )

        aggregated = aggregator.aggregate([first, second])

        self.assertIs(aggregated["results"][0], first)
        self.assertIs(aggregated["results"][1], second)
        self.assertEqual(len(aggregated["results"]), 2)

    def test_aggregate_parallel_results(self):
        aggregator = ResultAggregator()

        parallel_results = [
            aggregator.normalize(
                "skill-b",
                Result(task_id="TASK-000001", status="completed", text="B"),
            ),
            aggregator.normalize(
                "skill-a",
                Result(task_id="TASK-000001", status="completed", text="A"),
            ),
        ]

        aggregated = aggregator.aggregate(parallel_results)

        self.assertEqual(aggregated["status"], "completed")
        self.assertEqual(
            [item["skill"] for item in aggregated["results"]],
            ["skill-b", "skill-a"],
        )
        self.assertEqual(aggregated["data"], ["B", "A"])


if __name__ == "__main__":
    unittest.main()
