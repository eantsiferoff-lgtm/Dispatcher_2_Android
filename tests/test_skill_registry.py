import unittest
from datetime import datetime, timedelta, timezone

from core.skill_registry import SkillRegistry


class TestSkillRegistry(unittest.TestCase):

    def test_discovers_installed_skills(self):
        registry = SkillRegistry(".")

        skills = registry.all()
        skill_ids = [skill.skill_id for skill in skills]

        # Registry must discover installed Skills dynamically.
        self.assertGreater(len(skill_ids), 0)

        # Every discovered Skill must have a unique ID.
        self.assertEqual(len(skill_ids), len(set(skill_ids)))

    def test_domain_excludes_top_level_router(self):
        registry = SkillRegistry(".")

        top = registry.top_level()
        self.assertIsNotNone(top)

        domain_ids = {skill.skill_id for skill in registry.domain()}

        # Domain must exclude the dynamically discovered top-level router.
        self.assertNotIn(top.skill_id, domain_ids)

    def test_top_level_router(self):
        registry = SkillRegistry(".")

        top = registry.top_level()

        self.assertIsNotNone(top)
        self.assertEqual(top.metadata.get("role"), "top-level-router")

    def test_is_eligible_requires_active_domain_skill(self):
        registry = SkillRegistry("tests/fixtures")

        active = registry.get("test-skill")

        self.assertIsNotNone(active)
        self.assertTrue(registry.is_eligible(active))

        active.metadata["lifecycle"] = {
            "status": "dormant",
            "last_used_at": (
                datetime.now(timezone.utc) - timedelta(days=200)
            ).isoformat(),
        }

        self.assertFalse(registry.is_eligible(active))

    def test_discovers_new_skill_automatically(self):
        registry = SkillRegistry("tests/fixtures")

        skill = registry.get("test-skill")

        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "test-skill")


if __name__ == "__main__":
    unittest.main()
