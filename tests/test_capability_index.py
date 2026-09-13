import unittest
from datetime import datetime, timedelta, timezone

from core.capability_index import CapabilityIndex
from core.skill_registry import SkillRecord, SkillRegistry


class TestCapabilityIndex(unittest.TestCase):
    def test_excludes_inactive_skills(self):
        registry = SkillRegistry(".")
        active = registry.get("russian-investment-analysis")
        self.assertIsNotNone(active)

        dormant = SkillRecord(
            "dormant-test",
            "skills/dormant-test/SKILL.md",
            "Dormant Test",
            "Dormant test skill",
            {
                "capabilities": ["test"],
                "triggers": ["dormant"],
                "lifecycle": {
                    "status": "dormant",
                    "last_used_at": (
                        datetime.now(timezone.utc) - timedelta(days=200)
                    ).isoformat(),
                },
            },
        )

        registry._records["dormant-test"] = dormant

        index = CapabilityIndex(registry)
        skill_ids = {item.skill_id for item in index.build()}

        self.assertIn(active.skill_id, skill_ids)
        self.assertNotIn("dormant-test", skill_ids)


if __name__ == "__main__":
    unittest.main()
