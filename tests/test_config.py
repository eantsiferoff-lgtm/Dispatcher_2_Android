import unittest
from pathlib import Path

from core.config import DispatcherConfig


class TestDispatcherConfig(unittest.TestCase):
    def test_loads_orchestration_and_verification(self):
        config = DispatcherConfig.from_file("dispatcher.yaml")

        self.assertTrue(config.allow_multi_skill)
        self.assertEqual(config.max_parallel_skills, 4)
        self.assertTrue(config.prefer_specific_skill)
        self.assertTrue(config.preserve_project_context)

        self.assertTrue(config.verification_required)
        self.assertTrue(config.check_conflicts)
        self.assertTrue(config.distinguish_facts_calculations_assumptions)

    def test_loads_registry_and_routing_paths(self):
        config = DispatcherConfig.from_file("dispatcher.yaml")

        self.assertEqual(config.registry_path, "registry.yaml")
        self.assertEqual(config.routing_path, "routing.yaml")


    def test_loads_workflows(self):
        config_path = "tests/tmp_dispatcher_workflow.yaml"
        Path(config_path).write_text(
            """version: "2.0"
workflows:
  market-report:
    steps:
      - skill: skill-a
        depends_on: []
        execution_mode: parallel
      - skill: skill-b
        depends_on: [1]
        execution_mode: ordered
""",
            encoding="utf-8",
        )

        try:
            config = DispatcherConfig.from_file(config_path)

            self.assertIn("market-report", config.workflows)
            self.assertEqual(
                config.workflows["market-report"]["steps"][0]["execution_mode"],
                "parallel",
            )
        finally:
            Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
