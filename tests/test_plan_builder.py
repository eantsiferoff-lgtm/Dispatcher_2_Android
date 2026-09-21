from pathlib import Path
import unittest

from core.plan_builder import PlanBuilder
from core.planner import PlannerDecision


class TestPlanBuilder(unittest.TestCase):
    def test_builds_ordered_steps_with_dependency_metadata(self):
        decision = PlannerDecision(
            skills=["skill-a", "skill-b"],
            confidence=1.0,
        )

        plan = PlanBuilder().build("req_001", decision)

        self.assertEqual(plan.skills, ["skill-a", "skill-b"])
        self.assertEqual(len(plan.steps), 2)

        self.assertEqual(plan.steps[0]["step"], 1)
        self.assertEqual(plan.steps[0]["skill"], "skill-a")
        self.assertEqual(plan.steps[0]["status"], "pending")
        self.assertEqual(plan.steps[0]["depends_on"], [])
        self.assertEqual(plan.steps[0]["execution_mode"], "ordered")

        self.assertEqual(plan.steps[1]["step"], 2)
        self.assertEqual(plan.steps[1]["skill"], "skill-b")
        self.assertEqual(plan.steps[1]["status"], "pending")
        self.assertEqual(plan.steps[1]["depends_on"], [1])
        self.assertEqual(plan.steps[1]["execution_mode"], "ordered")


    def test_builds_step_from_skill_metadata(self):
        from core.skill_registry import SkillRegistry

        registry = SkillRegistry("tests/fixtures")

        skill = registry.get("test-skill")
        self.assertIsNotNone(skill)

        skill.metadata["backend"] = "openai"
        skill.metadata["execution_mode"] = "ai"

        decision = PlannerDecision(
            skills=["test-skill"],
            confidence=1.0,
        )

        plan = PlanBuilder(registry=registry).build(
            "req_metadata_001",
            decision,
        )

        self.assertEqual(plan.steps[0]["skill"], "test-skill")
        self.assertEqual(plan.steps[0]["backend"], "openai")
        self.assertEqual(plan.steps[0]["execution_mode"], "ai")

    def test_builds_step_from_dynamically_added_skill_metadata(self):
        import tempfile

        from core.skill_registry import SkillRegistry

        with tempfile.TemporaryDirectory() as root:
            skill_dir = Path(root) / "skills" / "dynamic-test-skill"
            skill_dir.mkdir(parents=True)

            (skill_dir / "SKILL.md").write_text(
                """---
name: dynamic-test-skill
description: Perform dynamic document verification.
metadata:
  version: "1.0"
  capabilities:
    - document-verification
  triggers:
    - проверь документ
  execution_mode: ordered
  backend: local
---
# Dynamic Test Skill

Created dynamically for the extensibility test.
""",
                encoding="utf-8",
            )

            registry = SkillRegistry(root)
            skill = registry.get("dynamic-test-skill")

            self.assertIsNotNone(skill)

            decision = PlannerDecision(
                skills=["dynamic-test-skill"],
                confidence=1.0,
            )

            plan = PlanBuilder(registry=registry).build(
                "req_dynamic_001",
                decision,
            )

            self.assertEqual(
                plan.steps[0]["skill"],
                "dynamic-test-skill",
            )
            self.assertEqual(
                plan.steps[0]["backend"],
                "local",
            )
            self.assertEqual(
                plan.steps[0]["execution_mode"],
                "ordered",
            )

    def test_builds_composio_step_with_tool_slug(self):
        decision = PlannerDecision(
            skills=["github"],
            confidence=1.0,
        )

        workflow = {
            "github": {
                "depends_on": [],
                "execution_mode": "ordered",
                "backend": "composio",
                "tool_slug": "GITHUB_GET_THE_AUTHENTICATED_USER",
            },
        }

        plan = PlanBuilder().build(
            "req_composio_001",
            decision,
            workflow=workflow,
        )

        self.assertEqual(
            plan.steps[0]["backend"],
            "composio",
        )
        self.assertEqual(
            plan.steps[0]["tool_slug"],
            "GITHUB_GET_THE_AUTHENTICATED_USER",
        )

    def test_builds_n8n_step_with_workflow(self):
        decision = PlannerDecision(
            skills=["n8n"],
            confidence=1.0,
        )

        workflow = {
            "n8n": {
                "depends_on": [],
                "execution_mode": "ordered",
                "backend": "n8n",
                "workflow": "market-analysis",
            },
        }

        plan = PlanBuilder().build(
            "req_n8n_001",
            decision,
            workflow=workflow,
        )

        self.assertEqual(plan.steps[0]["backend"], "n8n")
        self.assertEqual(plan.steps[0]["workflow"], "market-analysis")

    def test_builds_dag_steps_from_workflow_metadata(self):
        decision = PlannerDecision(
            skills=["skill-a", "skill-b", "skill-c"],
            confidence=1.0,
        )

        workflow = {
            "skill-a": {"depends_on": [], "execution_mode": "parallel"},
            "skill-b": {"depends_on": [], "execution_mode": "parallel"},
            "skill-c": {"depends_on": [1, 2], "execution_mode": "ordered"},
        }

        plan = PlanBuilder().build("req_dag_001", decision, workflow=workflow)

        self.assertEqual(plan.steps[0]["depends_on"], [])
        self.assertEqual(plan.steps[0]["execution_mode"], "parallel")
        self.assertEqual(plan.steps[1]["depends_on"], [])
        self.assertEqual(plan.steps[1]["execution_mode"], "parallel")
        self.assertEqual(plan.steps[2]["depends_on"], [1, 2])
        self.assertEqual(plan.steps[2]["execution_mode"], "ordered")


if __name__ == "__main__":
    unittest.main()
