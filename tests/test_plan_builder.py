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
