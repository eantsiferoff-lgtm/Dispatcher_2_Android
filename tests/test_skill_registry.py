from pathlib import Path
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

    def test_discovers_skill_added_without_core_changes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            skill_dir = Path(root) / "skills" / "new-skill"
            skill_dir.mkdir(parents=True)

            (skill_dir / "SKILL.md").write_text(
                """---
name: new-skill
description: A dynamically added test skill.
metadata:
  capabilities:
    - test-capability
  triggers:
    - run new skill
---
# New Skill

This Skill is created only for the extensibility test.
""",
                encoding="utf-8",
            )

            registry = SkillRegistry(root)
            skill = registry.get("new-skill")

            self.assertIsNotNone(skill)
            self.assertEqual(skill.name, "new-skill")
            self.assertIn(
                "test-capability",
                skill.metadata.get("capabilities", []),
            )

    def test_discovers_new_skill_automatically(self):
        registry = SkillRegistry("tests/fixtures")

        skill = registry.get("test-skill")

        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "test-skill")



    def test_delete_skill_and_restore(self):
        registry = SkillRegistry("tests/fixtures")
        skill = registry.get("test-skill")

        self.assertIsNotNone(skill)
        self.assertTrue(registry.is_eligible(skill))

        deleted = registry.delete_skill("test-skill")

        self.assertIsNotNone(deleted)
        self.assertEqual(deleted.lifecycle_status, "deleted")
        self.assertFalse(registry.is_eligible(deleted))
        self.assertNotIn(
            "test-skill",
            {item.skill_id for item in registry.active_domain()},
        )

        restored = registry.restore_skill("test-skill")

        self.assertIsNotNone(restored)
        self.assertEqual(restored.lifecycle_status, "active")
        self.assertTrue(registry.is_eligible(restored))

    def test_skill_add_remove_and_rediscover_without_core_changes(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as root:
            skill_dir = Path(root) / "skills" / "dynamic-lifecycle-skill"
            skill_dir.mkdir(parents=True)

            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                """---
name: dynamic-lifecycle-skill
description: Skill for add/remove extensibility testing.
metadata:
  capabilities:
    - lifecycle-test
  triggers:
    - lifecycle test
---
# Dynamic Lifecycle Skill
Used only for extensibility lifecycle testing.
""",
                encoding="utf-8",
            )

            # ADD → DISCOVER
            registry = SkillRegistry(root)
            self.assertIsNotNone(
                registry.get("dynamic-lifecycle-skill")
            )

            # REMOVE
            skill_file.unlink()
            skill_dir.rmdir()

            # Re-create Registry to simulate a fresh discovery cycle.
            registry = SkillRegistry(root)
            self.assertIsNone(
                registry.get("dynamic-lifecycle-skill")
            )

            # ADD AGAIN → DISCOVER AGAIN
            new_skill_dir = Path(root) / "skills" / "dynamic-lifecycle-skill-2"
            new_skill_dir.mkdir(parents=True)

            (new_skill_dir / "SKILL.md").write_text(
                """---
name: dynamic-lifecycle-skill-2
description: Replacement dynamically discovered skill.
metadata:
  capabilities:
    - lifecycle-test-2
  triggers:
    - lifecycle test 2
---
# Dynamic Lifecycle Skill 2
Replacement skill for extensibility testing.
""",
                encoding="utf-8",
            )

            registry = SkillRegistry(root)
            self.assertIsNotNone(
                registry.get("dynamic-lifecycle-skill-2")
            )

if __name__ == "__main__":
    unittest.main()
