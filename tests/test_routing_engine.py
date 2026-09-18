import unittest

from core.routing_engine import RoutingEngine
from core.skill_registry import SkillRegistry

class TestRoutingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RoutingEngine("routing.yaml", SkillRegistry("."))

    def test_routes_investment_request(self):
        self.assertEqual(self.engine.route("акции"), ["russian-investment-analysis"])

    def test_routes_pharmacy_request(self):
        self.assertEqual(self.engine.route("цена препарата"), ["pharmacy-and-supplements"])

    def test_routes_multiple_matching_rules(self):
        self.assertEqual(self.engine.route("аптека рядом с отелем"), ["pharmacy-and-supplements", "travel-local-search"])

if __name__ == "__main__":
    unittest.main()
