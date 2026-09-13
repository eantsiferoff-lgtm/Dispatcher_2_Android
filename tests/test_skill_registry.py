import unittest

from core.skill_registry import SkillRegistry


class TestSkillRegistry(unittest.TestCase):
    def test_discovers_all_installed_skills(self):
        registry = SkillRegistry(".")
        skill_ids = {skill.skill_id for skill in registry.all()}

        expected = {
            "1c-ut-documents",
            "file-project-analysis",
            "grants-and-project-applications",
            "image-editing-workflow",
            "official-documents",
            "pharmacy-and-supplements",
            "russian-investment-analysis",
            "travel-local-search",
            "workflow-dispatcher",
        }

        self.assertTrue(expected.issubset(skill_ids))

    def test_domain_excludes_top_level_router(self):
        registry = SkillRegistry(".")
        domain_ids = {skill.skill_id for skill in registry.domain()}

        self.assertEqual(len(domain_ids), 8)
        self.assertNotIn("workflow-dispatcher", domain_ids)

    def test_top_level_router(self):
        registry = SkillRegistry(".")
        top = registry.top_level()

        self.assertIsNotNone(top)
        self.assertEqual(top.skill_id, "workflow-dispatcher")

    def test_is_eligible_requires_active_domain_skill(self):
        registry = SkillRegistry("tests/fixtures")

        active = registry.get("test-skill")
        self.assertIsNotNone(active)
        self.assertTrue(registry.is_eligible(active))

        from datetime import datetime, timedelta, timezone

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
