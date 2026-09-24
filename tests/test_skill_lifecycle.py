import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.skill_lifecycle import SkillLifecycleManager
from core.skill_lifecycle_store import JsonSkillLifecycleStore
from core.skill_registry import SkillRecord, SkillRegistry


class TestSkillLifecycle(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 12, tzinfo=timezone.utc)
        self.manager = SkillLifecycleManager()

    def test_new_skill_is_active(self):
        self.assertEqual(self.manager.status({}, now=self.now), "active")

    def test_skill_becomes_dormant_after_180_days(self):
        meta = {
            "lifecycle": {
                "last_used_at": (self.now - timedelta(days=200)).isoformat()
            }
        }
        self.assertEqual(self.manager.status(meta, now=self.now), "dormant")

    def test_skill_becomes_archived_after_365_days(self):
        meta = {
            "lifecycle": {
                "last_used_at": (self.now - timedelta(days=400)).isoformat()
            }
        }
        self.assertEqual(self.manager.status(meta, now=self.now), "archived")

    def test_deleted_status_is_terminal(self):
        meta = {"lifecycle": {"status": "deleted"}}
        self.assertEqual(self.manager.status(meta, now=self.now), "deleted")

    def test_unknown_status_does_not_override_time_based_lifecycle(self):
        meta = {
            "lifecycle": {
                "status": "unknown",
                "last_used_at": (
                    self.now - timedelta(days=200)
                ).isoformat(),
            }
        }
        self.assertEqual(self.manager.status(meta, now=self.now), "dormant")

    def test_record_usage_updates_metadata(self):
        meta = {}
        self.manager.record_usage(meta, now=self.now)
        self.assertEqual(meta["lifecycle"]["status"], "active")
        self.assertEqual(meta["lifecycle"]["usage_count"], 1)
        self.assertEqual(meta["lifecycle"]["last_used_at"], self.now.isoformat())

    def test_restore_reactivates_skill(self):
        meta = {"lifecycle": {"status": "archived", "usage_count": 4}}
        self.manager.restore(meta, now=self.now)
        self.assertEqual(meta["lifecycle"]["status"], "active")
        self.assertEqual(meta["lifecycle"]["usage_count"], 4)
        self.assertEqual(meta["lifecycle"]["restored_count"], 1)

    def test_registry_excludes_dormant_skill(self):
        registry = SkillRegistry(".")
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {
                "lifecycle": {
                    "last_used_at": (self.now - timedelta(days=200)).isoformat()
                }
            },
        )
        registry._records = {"test-skill": skill}
        self.assertEqual(registry.active_domain(), [])

    def test_store_persists_state(self):
        path = Path("state/test_lifecycle.json")
        store = JsonSkillLifecycleStore(path)
        store.save("test-skill", {"status": "active", "usage_count": 2})
        self.assertEqual(store.load("test-skill")["usage_count"], 2)
        path.unlink(missing_ok=True)

    def test_planner_uses_skill_after_restore(self):
        from core.planner import Planner
        registry = SkillRegistry(".")
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {"triggers": ["уникальный тестовый запрос"], "lifecycle": {"status": "dormant", "last_used_at": (self.now - timedelta(days=200)).isoformat()}},
        )
        registry._records = {"test-skill": skill}
        self.assertEqual(Planner(registry).plan("уникальный тестовый запрос").skills, [])
        registry.restore_skill("test-skill")
        decision = Planner(registry).plan("уникальный тестовый запрос")
        self.assertIn("test-skill", decision.skills)

    def test_planner_excludes_dormant_skill(self):
        from core.planner import Planner
        registry = SkillRegistry(".")
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {"triggers": ["уникальный тестовый запрос"], "lifecycle": {"status": "dormant", "last_used_at": (self.now - timedelta(days=200)).isoformat()}},
        )
        registry._records = {"test-skill": skill}
        decision = Planner(registry).plan("уникальный тестовый запрос")
        self.assertNotIn("test-skill", decision.skills)
        self.assertEqual(decision.candidates, [])

    def test_full_lifecycle_active_dormant_archived_restore(self):
        registry = SkillRegistry(".")
        archived_at = (self.now - timedelta(days=400)).isoformat()
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {"lifecycle": {"status": "active", "last_used_at": archived_at}},
        )
        registry._records = {"test-skill": skill}
        self.assertEqual(skill.lifecycle_status, "archived")
        self.assertEqual(registry.active_domain(), [])
        restored = registry.restore_skill("test-skill")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.lifecycle_status, "active")
        self.assertEqual([item.skill_id for item in registry.active_domain()], ["test-skill"])

    def test_restore_returns_skill_to_active_domain(self):
        registry = SkillRegistry(".")
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {"lifecycle": {"status": "dormant", "last_used_at": (self.now - timedelta(days=200)).isoformat()}},
        )
        registry._records = {"test-skill": skill}
        self.assertEqual(registry.active_domain(), [])
        restored = registry.restore_skill("test-skill")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.lifecycle_status, "active")
        self.assertEqual([item.skill_id for item in registry.active_domain()], ["test-skill"])

    def test_runtime_automatically_refreshes_lifecycle(self):
        from core.runtime import Runtime
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_src = Path("skills/russian-investment-analysis")
            skill_dst = root / "skills" / "russian-investment-analysis"
            skill_dst.parent.mkdir(parents=True)
            shutil.copytree(skill_src, skill_dst)
            path = root / "state" / "skill_lifecycle.json"
            store = JsonSkillLifecycleStore(path)
            old_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
            store.save("russian-investment-analysis", {"status": "active", "last_used_at": old_date, "usage_count": 3})
            runtime = Runtime(root, auto_refresh_lifecycle=True)
        skill = runtime.registry.get("russian-investment-analysis")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.lifecycle_status, "dormant")
        path.unlink(missing_ok=True)

    def test_registry_restores_archived_state_from_store(self):
        path = Path("state/test_lifecycle.json")
        store = JsonSkillLifecycleStore(path)
        store.save(
            "russian-investment-analysis",
            {
                "status": "archived",
                "last_used_at": "2025-01-01T00:00:00+00:00",
                "usage_count": 8,
            },
        )
        registry = SkillRegistry(".", lifecycle_store=store)
        skill = registry.get("russian-investment-analysis")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.lifecycle_status, "archived")
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
