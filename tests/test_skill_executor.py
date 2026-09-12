import unittest

from core.skill_executor import SkillExecutor


class TestSkillExecutor(unittest.TestCase):
    def test_register_and_execute_handler(self):
        executor = SkillExecutor()

        def handler(step, task):
            return {"text": f"executed:{step['skill']}"}

        executor.register("test-skill", handler)

        result = executor.execute(
            {
                "skill": "test-skill",
                "step": 1,
            },
            task_id="task_001",
        )

        self.assertEqual(result["text"], "executed:test-skill")


    def test_reports_missing_handler(self):
        executor = SkillExecutor()
        self.assertFalse(executor.has_handler("unknown-skill"))


    def test_lists_registered_handlers(self):
        executor = SkillExecutor()
        executor.register("skill-a", lambda step, task_id: {})
        executor.register("skill-b", lambda step, task_id: {})
        self.assertEqual(set(executor.handler_ids()), {"skill-a", "skill-b"})


if __name__ == "__main__":
    unittest.main()
