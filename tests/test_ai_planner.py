import unittest

from core.ai_planner import AIPlanner
from core.skill_registry import SkillRegistry


class TestAIPlanner(unittest.TestCase):
    def test_returns_only_active_skills(self):
        from datetime import datetime, timedelta, timezone
        from core.skill_registry import SkillRecord
        registry = SkillRegistry(".")
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {"triggers": ["уникальный тестовый запрос"], "lifecycle": {"status": "dormant", "last_used_at": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()}},
        )
        registry._records = {"test-skill": skill}
        planner = AIPlanner(registry, runner=lambda request: ["test-skill"])
        self.assertEqual(planner.plan("уникальный тестовый запрос"), [])

    def test_returns_only_registered_skills(self):
        planner = AIPlanner(
            SkillRegistry("."),
            runner=lambda request: ["russian-investment-analysis", "fake-skill"],
        )
        result = planner.plan("сложный запрос")
        self.assertEqual(result, ["russian-investment-analysis"])


if __name__ == "__main__":
    unittest.main()
