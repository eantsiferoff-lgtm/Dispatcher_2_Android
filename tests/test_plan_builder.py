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


if __name__ == "__main__":
    unittest.main()
