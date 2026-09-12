import unittest

from core.execution_router import ExecutionRouter


class TestExecutionRouter(unittest.TestCase):
    def test_selects_registered_backend(self):
        router = ExecutionRouter()

        backend = object()
        router.register("test-backend", backend)

        selected = router.select("test-backend")

        self.assertIs(selected, backend)

    def test_unknown_backend_returns_none(self):
        router = ExecutionRouter()

        self.assertIsNone(router.select("unknown"))


    def test_executes_selected_backend(self):
        router = ExecutionRouter()

        class Backend:
            def execute(self, task):
                return {"status": "completed", "task_id": task["id"]}

        router.register("test-backend", Backend())
        result = router.execute("test-backend", {"id": "task_001"})

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["task_id"], "task_001")

    def test_unknown_backend_raises(self):
        router = ExecutionRouter()
        with self.assertRaises(KeyError):
            router.execute("unknown", {"id": "task_001"})


    def test_selects_highest_priority_available_backend(self):
        router = ExecutionRouter()
        class Backend:
            def __init__(self, priority, available):
                self.priority = priority
                self._available = available
            def available(self):
                return self._available

        low = Backend(10, True)
        high = Backend(100, True)
        low.priority = 10
        high.priority = 100
        low.available = lambda: True
        high.available = lambda: True
        router.register("low", low)
        router.register("high", high)
        self.assertIs(router.select_available(), high)

    def test_returns_none_when_no_backend_available(self):
        router = ExecutionRouter()
        self.assertIsNone(router.select_available())


    def test_routes_step_to_highest_priority_backend(self):
        router = ExecutionRouter()

        class Backend:
            def __init__(self, priority):
                self.priority = priority
            def available(self):
                return True
            def execute(self, task):
                return {"backend": self.priority, "status": "completed"}

        router.register("low", Backend(10))
        router.register("high", Backend(100))

        result = router.route({"skill": "russian-investment-analysis"})

        self.assertEqual(result, "high")


    def test_route_uses_backend_can_execute(self):
        router = ExecutionRouter()

        class Backend:
            priority = 100
            def available(self):
                return True
            def can_execute(self, task):
                return task.get("skill") == "supported-skill"
            def execute(self, task):
                return {"status": "completed"}

        router.register("supported", Backend())

        self.assertEqual(
            router.route({"skill": "supported-skill"}),
            "supported",
        )
        self.assertIsNone(
            router.route({"skill": "other-skill"})
        )


    def test_route_filters_backends_by_can_execute(self):
        router = ExecutionRouter()

        class Backend:
            priority = 100
            def __init__(self, supported):
                self.supported = supported
            def available(self):
                return True
            def can_execute(self, task):
                return task.get("skill") in self.supported

        router.register("wrong", Backend({"other-skill"}))
        router.register("right", Backend({"test-skill"}))

        self.assertEqual(router.route({"skill": "test-skill"}), "right")
        self.assertIsNone(router.route({"skill": "unknown-skill"}))


if __name__ == "__main__":
    unittest.main()
