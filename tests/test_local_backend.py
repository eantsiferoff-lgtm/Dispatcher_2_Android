import unittest

from core.local_backend import LocalBackend


class TestLocalBackend(unittest.TestCase):
    def test_executes_registered_skill(self):
        calls = []

        def handler(step, task_id):
            calls.append((step["skill"], task_id))
            return {"text": "ok"}

        backend = LocalBackend()
        backend.register("test-skill", handler)

        result = backend.execute({"skill": "test-skill"}, "task_001")

        self.assertEqual(result["text"], "ok")
        self.assertEqual(calls, [("test-skill", "task_001")])


if __name__ == "__main__":
    unittest.main()
