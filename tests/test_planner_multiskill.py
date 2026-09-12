import unittest

from core.planner import Planner
from core.skill_registry import SkillRegistry


class TestPlannerMultiSkill(unittest.TestCase):
    def setUp(self):
        self.planner = Planner(SkillRegistry("."))

    def test_investment_plus_files(self):
        decision = self.planner.plan(
            "Проанализируй российский фондовый рынок по файлам проекта"
        )

        self.assertIn("russian-investment-analysis", decision.skills)
        self.assertIn("file-project-analysis", decision.skills)

    def test_pharmacy_and_local_search(self):
        decision = self.planner.plan(
            "Найди аптеку рядом"
        )

        self.assertIn("travel-local-search", decision.skills)


if __name__ == "__main__":
    unittest.main()
