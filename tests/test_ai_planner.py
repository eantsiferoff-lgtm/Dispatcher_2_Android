import unittest

from core.ai_planner import AIPlanner
from core.skill_registry import SkillRegistry


class TestAIPlanner(unittest.TestCase):
    def test_returns_only_registered_skills(self):
        planner = AIPlanner(
            SkillRegistry("."),
            runner=lambda request: ["russian-investment-analysis", "fake-skill"],
        )
        result = planner.plan("сложный запрос")
        self.assertEqual(result, ["russian-investment-analysis"])


if __name__ == "__main__":
    unittest.main()
