import unittest

from core.models import Request, Plan, Task
from core.runtime import Runtime
from core.skill_executor import SkillExecutor


class TestRuntime(unittest.TestCase):
    def test_uses_default_config_when_file_is_missing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root)
            self.assertEqual(runtime.config.max_parallel_skills, 4)
            self.assertTrue(runtime.config.allow_multi_skill)

    def test_loads_dispatcher_config(self):
        runtime = Runtime(".")
        self.assertEqual(runtime.config.max_parallel_skills, 4)
        self.assertTrue(runtime.config.allow_multi_skill)
        self.assertEqual(runtime.config.registry_path, "registry.yaml")
        self.assertEqual(runtime.config.routing_path, "routing.yaml")

    def test_registers_openai_backend_when_factory_provided(self):
        from core.openai_backend import OpenAIBackend
        runtime = Runtime(".", openai_runner=lambda text: "ok")
        backend = runtime.execution_router.select("openai")
        self.assertIsInstance(backend, OpenAIBackend)
        self.assertEqual(backend.priority, 10)

    def test_multi_skill_plan_preserves_skill_order_and_dependencies(self):
        runtime = Runtime(".")
        request, plan, task = runtime.prepare(
            "Проанализируй российский фондовый рынок по файлам проекта"
        )

        self.assertIn("russian-investment-analysis", plan.skills)
        self.assertIn("file-project-analysis", plan.skills)
        self.assertEqual(len(plan.steps), 2)

        self.assertEqual(plan.steps[0]["step"], 1)
        self.assertEqual(plan.steps[1]["step"], 2)
        self.assertEqual(plan.steps[0]["status"], "pending")
        self.assertEqual(plan.steps[1]["status"], "pending")

        self.assertIn("depends_on", plan.steps[0])
        self.assertIn("depends_on", plan.steps[1])
        self.assertIn("execution_mode", plan.steps[0])
        self.assertIn("execution_mode", plan.steps[1])


    def test_prepare_creates_request_plan_and_task(self):
        runtime = Runtime(".")
        request, plan, task = runtime.prepare("Проанализируй российский фондовый рынок")

        self.assertIsInstance(request, Request)
        self.assertIsInstance(plan, Plan)
        self.assertIsInstance(task, Task)

        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertIn("russian-investment-analysis", plan.skills)
        self.assertEqual(task.request_id, request.request_id)
        self.assertIs(task.plan, plan)
        self.assertEqual(task.status, "pending")


    def test_run_executes_full_pipeline(self):
        skill_executor = SkillExecutor()
        skill_executor.register("russian-investment-analysis", lambda step, task_id: {"text": "ok"})
        runtime = Runtime(".", skill_executor=skill_executor)
        request, plan, task, result = runtime.run("Проанализируй российский фондовый рынок")
        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertIn("russian-investment-analysis", plan.skills)
        self.assertEqual(task.status, "completed")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.task_id, task.task_id)


    def test_run_uses_execution_router_backend(self):
        from core.execution_router import ExecutionRouter

        class Backend:
            priority = 100

            def available(self):
                return True

            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id}

        router = ExecutionRouter()
        router.register("test", Backend())

        runtime = Runtime(".", execution_router=router)

        request, plan, task = runtime.prepare(
            "Проанализируй российский фондовый рынок"
        )
        plan.steps[0]["backend"] = "test"

        result = runtime.executor.execute(task)

        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.task_id, task.task_id)
        self.assertEqual(task.status, "completed")


    def test_run_auto_uses_local_backend(self):
        from core.execution_router import ExecutionRouter
        from core.local_backend import LocalBackend
        from core.skill_executor import SkillExecutor

        skills = SkillExecutor()
        calls = []

        def handler(step, task_id):
            calls.append((step["skill"], task_id))
            return {"text": "ok"}

        skills.register("russian-investment-analysis", handler)
        local = LocalBackend(skills)
        router = ExecutionRouter()
        router.register("local", local)

        runtime = Runtime(".", execution_router=router)
        request, plan, task = runtime.prepare("Проанализируй российский фондовый рынок")
        result = runtime.executor.execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(calls[0][0], "russian-investment-analysis")


    def test_auto_refresh_lifecycle_can_be_enabled_or_disabled(self):
        runtime_on = Runtime(".", auto_refresh_lifecycle=True)
        runtime_off = Runtime(".", auto_refresh_lifecycle=False)
        self.assertTrue(runtime_on.auto_refresh_lifecycle)
        self.assertFalse(runtime_off.auto_refresh_lifecycle)

    def test_prepare_preserves_attachments_and_project(self):
        runtime = Runtime(".")
        request, plan, task = runtime.prepare(
            "Проанализируй рынок по файлам проекта",
            attachments=["/tmp/report.pdf", "/tmp/data.xlsx"],
            project_id="project_001",
        )

        self.assertEqual(
            request.attachments,
            ["/tmp/report.pdf", "/tmp/data.xlsx"],
        )
        self.assertEqual(request.project_id, "project_001")
        self.assertEqual(task.project_id, "project_001")
        self.assertEqual(task.status, "pending")


if __name__ == "__main__":
    unittest.main()
