import unittest

from core.models import Result
from core.verification import VerificationLayer


class TestVerificationLayer(unittest.TestCase):
    def test_verification_result_contract(self):
        result = Result(
            task_id="TASK-000001",
            status="completed",
            text="Готово",
        )

        verification = VerificationLayer()
        report = verification.verify(result)

        self.assertIn("status", report)
        self.assertIn("checks", report)
        self.assertIsInstance(report["checks"], list)

    def test_verification_check_types(self):
        result = Result(
            task_id="TASK-000001",
            status="completed",
            text="Готово",
        )

        report = VerificationLayer().verify(result)

        allowed_types = {
            "FACT",
            "CALCULATION",
            "ASSUMPTION",
            "CONFLICT",
            "WARNING",
        }

        for check in report["checks"]:
            self.assertIn(check["type"], allowed_types)

    def test_failed_result_creates_warning(self):
        result = Result(
            task_id="TASK-000001",
            status="failed",
            text="",
            warnings=["execution failed"],
        )

        report = VerificationLayer().verify(result)

        warnings = [
            check
            for check in report["checks"]
            if check["type"] == "WARNING"
        ]

        self.assertEqual(len(warnings), 1)
        self.assertIn("execution failed", warnings[0]["message"])
        self.assertEqual(warnings[0]["severity"], "warning")

    def test_completed_result_preserves_warnings(self):
        result = Result(
            task_id="TASK-000001",
            status="completed",
            text="Готово",
            warnings=["source is incomplete"],
        )

        report = VerificationLayer().verify(result)

        warnings = [
            check
            for check in report["checks"]
            if check["type"] == "WARNING"
        ]

        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["message"], "source is incomplete")



    def test_verification_can_be_disabled_by_config(self):
        from core.config import DispatcherConfig

        config = DispatcherConfig(
            registry_path="registry.yaml",
            routing_path="routing.yaml",
            allow_multi_skill=True,
            max_parallel_skills=4,
            prefer_specific_skill=True,
            preserve_project_context=True,
            verification_required=False,
            check_conflicts=True,
            distinguish_facts_calculations_assumptions=True,
            workflows={},
        )

        self.assertFalse(config.verification_required)

if __name__ == "__main__":
    unittest.main()

