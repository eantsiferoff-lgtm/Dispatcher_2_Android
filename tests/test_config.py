import unittest

from core.config import DispatcherConfig


class TestDispatcherConfig(unittest.TestCase):
    def test_loads_orchestration_and_verification(self):
        config = DispatcherConfig.from_file("dispatcher.yaml")

        self.assertTrue(config.allow_multi_skill)
        self.assertEqual(config.max_parallel_skills, 4)
        self.assertTrue(config.prefer_specific_skill)
        self.assertTrue(config.preserve_project_context)

        self.assertTrue(config.verification_required)
        self.assertTrue(config.check_conflicts)
        self.assertTrue(config.distinguish_facts_calculations_assumptions)

    def test_loads_registry_and_routing_paths(self):
        config = DispatcherConfig.from_file("dispatcher.yaml")

        self.assertEqual(config.registry_path, "registry.yaml")
        self.assertEqual(config.routing_path, "routing.yaml")


if __name__ == "__main__":
    unittest.main()
