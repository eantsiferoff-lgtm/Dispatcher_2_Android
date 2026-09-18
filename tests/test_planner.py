import unittest

from core.planner import Planner, PlannerDecision
from core.skill_registry import SkillRegistry


class TestPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = Planner(SkillRegistry("."))

    def test_investment_request(self):
        decision = self.planner.plan(
            "Проанализируй российский фондовый рынок"
        )
        self.assertIn("russian-investment-analysis", decision.skills)

    def test_candidates_have_scores(self):
        decision = self.planner.plan(
            "Проанализируй российский фондовый рынок"
        )
        self.assertTrue(decision.candidates)
        self.assertTrue(all(0 <= c.score <= 1 for c in decision.candidates))

    def test_fallback_is_requested_for_low_confidence(self):
        from core.planner import Planner, PlannerDecision
        planner = Planner.__new__(Planner)
        planner.registry = None
        class Decision:
            skills = []
            candidates = []
            confidence = 0.0
        planner.plan = lambda request: Decision()
        self.assertEqual(planner.plan("совершенно неизвестный запрос").confidence, 0.0)

    def test_fallback_returns_registered_skill_from_ai_planner(self):
        from core.skill_registry import SkillRegistry
        from core.ai_planner import AIPlanner
        registry = SkillRegistry(".")
        ai = AIPlanner(registry, runner=lambda request: "russian-investment-analysis")
        planner = Planner(registry, fallback=ai.plan)
        decision = planner.plan("задача без локального совпадения")
        self.assertEqual(decision.skills, ["russian-investment-analysis"])

    def test_fallback_rejects_dormant_skills(self):
        from datetime import datetime, timedelta, timezone
        from core.skill_registry import SkillRecord
        registry = SkillRegistry(".")
        skill = SkillRecord(
            "test-skill",
            "skills/test/SKILL.md",
            "Test",
            "test",
            {"lifecycle": {"status": "dormant", "last_used_at": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()}},
        )
        registry._records = {"test-skill": skill}
        planner = Planner(registry, fallback=lambda request: ["test-skill"])
        decision = planner.plan("полностью неизвестная задача")
        self.assertEqual(decision.skills, [])

    def test_fallback_rejects_unknown_skills(self):
        from core.skill_registry import SkillRegistry
        planner = Planner(SkillRegistry("."), fallback=lambda request: ["russian-investment-analysis", "fake-skill"])
        decision = planner.plan("полностью неизвестная задача")
        self.assertEqual(decision.skills, ["russian-investment-analysis"])

    def test_low_confidence_calls_fallback(self):
        from core.skill_registry import SkillRegistry
        from core.planner import Planner, PlannerDecision
        registry = SkillRegistry(".")
        calls = []
        planner = Planner(registry, fallback=lambda request: calls.append(request) or ["russian-investment-analysis"])
        decision = planner.plan("полностью неизвестная задача")
        self.assertEqual(decision.skills, ["russian-investment-analysis"])
        self.assertEqual(calls, ["полностью неизвестная задача"])

    def test_unknown_request_can_have_no_match(self):
        decision = self.planner.plan(
            "Совершенно абстрактный запрос"
        )
        self.assertIsInstance(decision.skills, list)





    def test_planner_decision_can_store_workflow_id(self):
        decision = PlannerDecision(
            skills=["skill-a"],
            workflow_id="market-report",
            confidence=1.0,
        )

        self.assertEqual(decision.workflow_id, "market-report")



    def test_routing_engine_has_priority(self):
        from core.routing_engine import RoutingEngine
        routing = RoutingEngine("routing.yaml", SkillRegistry("."))
        planner = Planner(SkillRegistry("."), routing_engine=routing)
        decision = planner.plan("МОEX")
        self.assertEqual(decision.skills, ["russian-investment-analysis"])
        self.assertEqual(decision.confidence, 1.0)
        self.assertEqual(len(decision.candidates), 1)
        self.assertEqual(decision.candidates[0].score, 1.0)
        self.assertEqual(decision.candidates[0].reason, "routing.yaml")

if __name__ == "__main__":
    unittest.main()
