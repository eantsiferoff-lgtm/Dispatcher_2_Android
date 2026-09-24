import unittest
from pathlib import Path

from core.config import DispatcherConfig


class TestWorkflow(unittest.TestCase):

    def test_workflow_discovery(self):
        config_path = Path("tests/tmp_workflow_discovery.yaml")

        config_path.write_text(
            """version: "2.0"
workflows:
  investment-report:
    steps:
      - skill: file-project-analysis
        depends_on: []
        execution_mode: ordered
      - skill: russian-investment-analysis
        depends_on: [1]
        execution_mode: ordered
""",
            encoding="utf-8",
        )

        try:
            config = DispatcherConfig.from_file(config_path)

            self.assertIn(
                "investment-report",
                config.workflows,
            )
            self.assertEqual(
                len(config.workflows["investment-report"]["steps"]),
                2,
            )
            self.assertEqual(
                config.workflows["investment-report"]["steps"][0]["skill"],
                "file-project-analysis",
            )
        finally:
            config_path.unlink(missing_ok=True)

    def test_workflow_selection(self):
        config_path = Path("tests/tmp_workflow_selection.yaml")

        config_path.write_text(
            """version: "2.0"
workflows:
  investment-report:
    steps:
      - skill: file-project-analysis
        depends_on: []
        execution_mode: ordered
      - skill: russian-investment-analysis
        depends_on: [1]
        execution_mode: ordered
""",
            encoding="utf-8",
        )

        try:
            config = DispatcherConfig.from_file(config_path)

            selected_skills = {
                "file-project-analysis",
                "russian-investment-analysis",
            }

            matches = []

            for workflow_id, workflow in config.workflows.items():
                workflow_skills = {
                    step["skill"]
                    for step in workflow.get("steps", [])
                    if step.get("skill")
                }

                if workflow_skills == selected_skills:
                    matches.append(workflow_id)

            self.assertEqual(
                matches,
                ["investment-report"],
            )
        finally:
            config_path.unlink(missing_ok=True)
    def test_runtime_workflow_selection(self):
        from core.planner import PlannerDecision
        from core.runtime import Runtime

        runtime = Runtime(".")

        runtime.config = type(
            "Config",
            (),
            {
                "workflows": {
                    "investment-report": {
                        "steps": [
                            {"skill": "file-project-analysis"},
                            {"skill": "russian-investment-analysis"},
                        ]
                    }
                }
            },
        )()

        decision = PlannerDecision(
            skills=[
                "file-project-analysis",
                "russian-investment-analysis",
            ],
            confidence=1.0,
        )

        self.assertEqual(
            runtime._select_workflow(decision),
            "investment-report",
        )
    def test_unknown_workflow(self):
        from core.runtime import Runtime

        runtime = Runtime(".")

        self.assertEqual(
            runtime._workflow_metadata("unknown-workflow"),
            {},
        )


if __name__ == "__main__":
    unittest.main()
