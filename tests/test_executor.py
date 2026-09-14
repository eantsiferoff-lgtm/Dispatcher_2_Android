import unittest

from core.executor import Executor
from core.models import Plan, Task
from core.skill_executor import SkillExecutor
from core.security_policy import SecurityPolicy


class TestExecutor(unittest.TestCase):
    def test_executes_registered_skill_handlers(self):
        skill_executor = SkillExecutor()
        calls = []

        def handler(step, task_id):
            calls.append((step["skill"], task_id))
            return {"text": f"executed:{step['skill']}"}

        skill_executor.register(
            "russian-investment-analysis",
            handler,
        )

        plan = Plan(
            request_id="req_001",
            skills=["russian-investment-analysis"],
            steps=[
                {
                    "step": 1,
                    "skill": "russian-investment-analysis",
                    "status": "pending",
                }
            ],
        )

        task = Task(
            task_id="task_001",
            request_id="req_001",
            plan=plan,
        )

        result = Executor(skill_executor).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.current_step, 1)
        self.assertEqual(
            calls,
            [("russian-investment-analysis", "task_001")],
        )
        self.assertEqual(
            plan.steps[0]["status"],
            "completed",
        )


    def test_parallel_helper_executes_all_steps(self):
        from core.execution_router import ExecutionRouter
        from threading import Event

        started_a = Event()
        started_b = Event()
        release = Event()
        calls = []

        class Backend:
            priority = 100

            def available(self):
                return True

            def can_execute(self, step):
                return step.get("skill") in {"skill-a", "skill-b"}

            def execute(self, step, task_id):
                skill = step["skill"]
                calls.append(skill)
                if skill == "skill-a":
                    started_a.set()
                else:
                    started_b.set()

                if not release.wait(timeout=2):
                    raise RuntimeError("parallel helper timeout")

                return {"status": "completed", "task_id": task_id}

        router = ExecutionRouter()
        router.register("test", Backend())
        executor = Executor(execution_router=router)

        task = Task(
            task_id="task_parallel_helper",
            request_id="req_parallel_helper",
        )

        steps = [
            {
                "step": 1,
                "skill": "skill-a",
                "status": "pending",
                "depends_on": [],
                "execution_mode": "parallel",
                "backend": "test",
            },
            {
                "step": 2,
                "skill": "skill-b",
                "status": "pending",
                "depends_on": [],
                "execution_mode": "parallel",
                "backend": "test",
            },
        ]

        import threading
        results_holder = []

        worker = threading.Thread(
            target=lambda: results_holder.extend(
                executor._execute_parallel_steps(steps, task)
            )
        )
        worker.start()

        try:
            self.assertTrue(started_a.wait(timeout=2))
            self.assertTrue(started_b.wait(timeout=2))
        finally:
            release.set()

        worker.join(timeout=3)

        self.assertFalse(worker.is_alive())
        self.assertEqual(len(results_holder), 2)
        self.assertEqual(
            [result[0]["status"] for result in results_holder],
            ["completed", "completed"],
        )


    def test_parallel_group_then_ordered_step(self):
        from core.execution_router import ExecutionRouter

        calls = []

        class Backend:
            priority = 100

            def available(self):
                return True

            def can_execute(self, step):
                return step.get("skill") in {"skill-a", "skill-b", "skill-c"}

            def execute(self, step, task_id):
                calls.append(step["skill"])
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "text": step["skill"],
                }

        router = ExecutionRouter()
        router.register("test", Backend())
        executor = Executor(execution_router=router)

        task = Task(
            task_id="task_mixed_execution",
            request_id="req_mixed_execution",
        )
        task.plan = type("Plan", (), {})()
        task.plan.steps = [
            {
                "step": 1,
                "skill": "skill-a",
                "status": "pending",
                "depends_on": [],
                "execution_mode": "parallel",
                "backend": "test",
            },
            {
                "step": 2,
                "skill": "skill-b",
                "status": "pending",
                "depends_on": [],
                "execution_mode": "parallel",
                "backend": "test",
            },
            {
                "step": 3,
                "skill": "skill-c",
                "status": "pending",
                "depends_on": [1, 2],
                "execution_mode": "ordered",
                "backend": "test",
            },
        ]

        result = executor.execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(calls, ["skill-a", "skill-b", "skill-c"])
        self.assertEqual(task.plan.steps[0]["status"], "completed")
        self.assertEqual(task.plan.steps[1]["status"], "completed")
        self.assertEqual(task.plan.steps[2]["status"], "completed")

    def test_parallel_group_uses_scheduler_ready_steps(self):
        from core.execution_router import ExecutionRouter

        calls = []

        class Backend:
            priority = 100

            def available(self):
                return True

            def can_execute(self, step):
                return step.get("skill") in {"skill-a", "skill-b", "skill-c"}

            def execute(self, step, task_id):
                calls.append(step["skill"])
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "text": step["skill"],
                }

        router = ExecutionRouter()
        router.register("test", Backend())
        executor = Executor(max_parallel_skills=2, execution_router=router)

        plan = Plan(
            request_id="req_scheduler_capacity",
            skills=["skill-a", "skill-b", "skill-c"],
            steps=[
                {
                    "step": 1,
                    "skill": "skill-a",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
                {
                    "step": 2,
                    "skill": "skill-b",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
                {
                    "step": 3,
                    "skill": "skill-c",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
            ],
        )

        task = Task(
            task_id="task_scheduler_capacity",
            request_id="req_scheduler_capacity",
            plan=plan,
        )

        result = executor.execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            [step["status"] for step in task.plan.steps],
            ["completed", "completed", "completed"],
        )
        self.assertCountEqual(calls, ["skill-a", "skill-b", "skill-c"])

    def test_executes_steps_by_dag_readiness(self):
        from core.execution_router import ExecutionRouter

        calls = []

        class Backend:
            priority = 100

            def available(self):
                return True

            def can_execute(self, step):
                return step.get("skill") in {"skill-a", "skill-b", "skill-c"}

            def execute(self, step, task_id):
                calls.append(step["skill"])
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "text": step["skill"],
                }

        router = ExecutionRouter()
        router.register("test", Backend())
        executor = Executor(max_parallel_skills=2, execution_router=router)

        plan = Plan(
            request_id="req_dag",
            skills=["skill-a", "skill-b", "skill-c"],
            steps=[
                {
                    "step": 1,
                    "skill": "skill-a",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
                {
                    "step": 2,
                    "skill": "skill-b",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
                {
                    "step": 3,
                    "skill": "skill-c",
                    "status": "pending",
                    "depends_on": [1, 2],
                    "execution_mode": "ordered",
                    "backend": "test",
                },
            ],
        )

        task = Task(
            task_id="task_dag",
            request_id="req_dag",
            plan=plan,
        )

        result = executor.execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(calls, ["skill-a", "skill-b", "skill-c"])
        self.assertEqual(
            [step["status"] for step in task.plan.steps],
            ["completed", "completed", "completed"],
        )

    def test_uses_dag_scheduler_for_ready_steps(self):
        executor = Executor(max_parallel_skills=2)

        self.assertIsNotNone(executor.dag_scheduler)
        self.assertEqual(executor.dag_scheduler.max_parallel_skills, 2)

    def test_accepts_max_parallel_skills(self):
        executor = Executor(max_parallel_skills=2)
        self.assertEqual(executor.max_parallel_skills, 2)

    def test_executes_independent_steps_in_parallel(self):
        from core.execution_router import ExecutionRouter
        from threading import Event

        started_a = Event()
        started_b = Event()
        release = Event()
        calls = []

        class Backend:
            priority = 100

            def available(self):
                return True

            def can_execute(self, step):
                return step.get("skill") in {"skill-a", "skill-b"}

            def execute(self, step, task_id):
                skill = step["skill"]
                calls.append(skill)
                if skill == "skill-a":
                    started_a.set()
                else:
                    started_b.set()

                if not release.wait(timeout=2):
                    raise RuntimeError("parallel execution timeout")

                return {"status": "completed", "task_id": task_id, "text": skill}

        router = ExecutionRouter()
        router.register("test", Backend())

        plan = Plan(
            request_id="req_parallel",
            skills=["skill-a", "skill-b"],
            steps=[
                {
                    "step": 1,
                    "skill": "skill-a",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
                {
                    "step": 2,
                    "skill": "skill-b",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                },
            ],
        )

        task = Task(
            task_id="task_parallel",
            request_id="req_parallel",
            plan=plan,
        )

        import threading
        worker = threading.Thread(
            target=lambda: Executor(execution_router=router).execute(task)
        )
        worker.start()

        try:
            self.assertTrue(started_a.wait(timeout=2))
            self.assertTrue(started_b.wait(timeout=2))
        finally:
            release.set()

        worker.join(timeout=3)

        self.assertFalse(worker.is_alive())
        self.assertCountEqual(calls, ["skill-a", "skill-b"])
        self.assertEqual(task.status, "completed")


    def test_uses_execution_router_backend(self):
        from core.execution_router import ExecutionRouter

        class Backend:
            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id}

        router = ExecutionRouter()
        router.register("test", Backend())

        plan = Plan(
            request_id="req_002",
            skills=["test-skill"],
            steps=[
                {
                    "step": 1,
                    "skill": "test-skill",
                    "backend": "test",
                    "status": "pending",
                }
            ],
        )

        task = Task(
            task_id="task_002",
            request_id="req_002",
            plan=plan,
        )

        result = Executor(execution_router=router).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.task_id, "task_002")
        self.assertEqual(task.status, "completed")

    def test_records_selected_backend(self):
        from core.execution_router import ExecutionRouter
        class Backend:
            priority = 100
            def available(self):
                return True
            def can_execute(self, step):
                return step.get("skill") == "test-skill"
            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id, "text": "ok"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_006", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "status": "pending"}])
        task = Task(task_id="task_006", request_id="req_006", plan=plan)
        result = Executor(execution_router=router).execute(task)
        self.assertEqual(result.status, "completed")
        self.assertEqual(plan.steps[0].get("backend"), "test")

    def test_passes_previous_step_result_to_next_step(self):
        from core.execution_router import ExecutionRouter
        calls = []
        class Backend:
            priority = 100
            def available(self):
                return True
            def can_execute(self, step):
                return step.get("skill") in {"skill-a", "skill-b"}
            def execute(self, step, task_id):
                calls.append(dict(step))
                if step["skill"] == "skill-a":
                    return {"status": "completed", "task_id": task_id, "text": "DATA_A"}
                return {"status": "completed", "task_id": task_id, "text": step.get("input", "") + "_PROCESSED"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_007", skills=["skill-a", "skill-b"], steps=[
            {"step": 1, "skill": "skill-a", "backend": "test", "status": "pending"},
            {"step": 2, "skill": "skill-b", "backend": "test", "status": "pending"},
        ])
        task = Task(task_id="task_007", request_id="req_007", plan=plan)
        result = Executor(execution_router=router).execute(task)
        self.assertEqual(result.status, "completed")
        self.assertEqual(calls[0]["skill"], "skill-a")
        self.assertEqual(calls[1].get("input"), "DATA_A")
        self.assertEqual(result.text, "DATA_A_PROCESSED")

    def test_preserves_backend_result_text(self):
        from core.execution_router import ExecutionRouter
        class Backend:
            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id, "text": "AI_RESULT"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_005", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "backend": "test", "status": "pending"}])
        task = Task(task_id="task_005", request_id="req_005", plan=plan)
        result = Executor(execution_router=router).execute(task)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.text, "AI_RESULT")

    def test_security_policy_allows_safe_action(self):
        from core.execution_router import ExecutionRouter
        from core.security_policy import SecurityPolicy
        calls = []
        class Backend:
            def execute(self, step, task_id):
                calls.append(step["action"])
                return {"status": "completed", "task_id": task_id, "text": "analyzed"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_010", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "action": "analyze", "backend": "test", "status": "pending"}])
        task = Task(task_id="task_010", request_id="req_010", plan=plan)
        result = Executor(execution_router=router, security_policy=SecurityPolicy()).execute(task)
        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(calls, ["analyze"])
        self.assertEqual(result.text, "analyzed")

    def test_records_failed_execution_trace(self):
        from core.execution_router import ExecutionRouter
        from core.execution_trace import ExecutionTrace
        trace = ExecutionTrace()
        class Backend:
            def execute(self, step, task_id):
                raise RuntimeError("backend boom")
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_012", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "action": "analyze", "backend": "test", "status": "pending"}])
        task = Task(task_id="task_012", request_id="req_012", plan=plan)
        result = Executor(execution_router=router, security_policy=SecurityPolicy(), execution_trace=trace).execute(task)
        self.assertEqual(result.status, "failed")
        events = trace.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "failed")
        self.assertEqual(events[0]["error"], "backend boom")

    def test_records_execution_trace(self):
        from core.execution_router import ExecutionRouter
        from core.execution_trace import ExecutionTrace
        trace = ExecutionTrace()
        class Backend:
            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id, "text": "ok"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_011", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "action": "analyze", "backend": "test", "status": "pending"}])
        task = Task(task_id="task_011", request_id="req_011", plan=plan)
        result = Executor(execution_router=router, security_policy=SecurityPolicy(), execution_trace=trace).execute(task)
        self.assertEqual(result.status, "completed")
        events = trace.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["request_id"], "req_011")
        self.assertEqual(events[0]["task_id"], "task_011")
        self.assertEqual(events[0]["skill"], "test-skill")
        self.assertEqual(events[0]["backend"], "test")
        self.assertEqual(events[0]["status"], "completed")

    def test_security_policy_denies_unknown_action(self):
        from core.execution_router import ExecutionRouter
        from core.security_policy import SecurityPolicy
        calls = []
        class Backend:
            def execute(self, step, task_id):
                calls.append(step)
                return {"status": "completed", "task_id": task_id, "text": "executed"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_009", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "action": "unknown-dangerous-action", "backend": "test", "status": "pending"}])
        task = Task(task_id="task_009", request_id="req_009", plan=plan)
        result = Executor(execution_router=router, security_policy=SecurityPolicy()).execute(task)
        self.assertEqual(result.status, "failed")
        self.assertEqual(task.status, "failed")
        self.assertEqual(calls, [])
        self.assertTrue(any("DENY" in warning for warning in result.warnings))

    def test_security_policy_blocks_consequential_action(self):
        from core.execution_router import ExecutionRouter
        from core.security_policy import SecurityPolicy
        calls = []
        class Backend:
            def execute(self, step, task_id):
                calls.append(step)
                return {"status": "completed", "task_id": task_id, "text": "sent"}
        router = ExecutionRouter()
        router.register("test", Backend())
        plan = Plan(request_id="req_008", skills=["test-skill"], steps=[{"step": 1, "skill": "test-skill", "action": "send", "backend": "test", "status": "pending"}])
        task = Task(task_id="task_008", request_id="req_008", plan=plan)
        result = Executor(execution_router=router, security_policy=SecurityPolicy()).execute(task)
        self.assertEqual(result.status, "failed")
        self.assertEqual(task.status, "failed")
        self.assertEqual(calls, [])
        self.assertTrue(any("CONFIRM" in warning for warning in result.warnings))

    def test_missing_execution_backend_fails_task(self):
        from core.execution_router import ExecutionRouter

        plan = Plan(
            request_id="req_003",
            skills=["test-skill"],
            steps=[
                {
                    "step": 1,
                    "skill": "test-skill",
                    "backend": "missing",
                    "status": "pending",
                }
            ],
        )

        task = Task(
            task_id="task_003",
            request_id="req_003",
            plan=plan,
        )

        result = Executor(execution_router=ExecutionRouter()).execute(task)

        self.assertEqual(result.status, "failed")
        self.assertEqual(task.status, "failed")


    def test_automatically_routes_when_backend_not_specified(self):
        from core.execution_router import ExecutionRouter

        class Backend:
            priority = 100
            def available(self):
                return True
            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id}

        router = ExecutionRouter()
        router.register("auto", Backend())

        plan = Plan(
            request_id="req_004",
            skills=["test-skill"],
            steps=[
                {
                    "step": 1,
                    "skill": "test-skill",
                    "status": "pending",
                }
            ],
        )

        task = Task(
            task_id="task_004",
            request_id="req_004",
            plan=plan,
        )

        result = Executor(execution_router=router).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")


    def test_executor_respects_max_parallel_skills(self):
        from core.execution_router import ExecutionRouter
        from threading import Event, Lock

        started = []
        active = 0
        max_active = 0
        lock = Lock()
        release_first_batch = Event()
        release_all = Event()

        class Backend:
            priority = 100

            def available(self):
                return True

            def can_execute(self, step):
                return step.get("skill", "").startswith("skill-")

            def execute(self, step, task_id):
                nonlocal active, max_active

                with lock:
                    started.append(step["skill"])
                    active += 1
                    max_active = max(max_active, active)

                if len(started) <= 4:
                    release_first_batch.wait(timeout=2)
                else:
                    release_all.wait(timeout=2)

                with lock:
                    active -= 1

                return {
                    "status": "completed",
                    "task_id": task_id,
                    "text": step["skill"],
                }

        router = ExecutionRouter()
        router.register("test", Backend())
        executor = Executor(max_parallel_skills=4, execution_router=router)

        plan = Plan(
            request_id="req_parallel_capacity",
            skills=[f"skill-{i}" for i in range(1, 6)],
            steps=[
                {
                    "step": i,
                    "skill": f"skill-{i}",
                    "status": "pending",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "backend": "test",
                }
                for i in range(1, 6)
            ],
        )

        task = Task(
            task_id="task_parallel_capacity",
            request_id="req_parallel_capacity",
            plan=plan,
        )

        import threading

        worker = threading.Thread(target=lambda: executor.execute(task))
        worker.start()

        try:
            for _ in range(100):
                with lock:
                    count = len(started)
                if count >= 4:
                    break
                threading.Event().wait(0.01)

            with lock:
                self.assertEqual(len(started), 4)
                self.assertEqual(max_active, 4)

            release_first_batch.set()

            for _ in range(100):
                with lock:
                    count = len(started)
                if count >= 5:
                    break
                threading.Event().wait(0.01)

            with lock:
                self.assertEqual(len(started), 5)
                self.assertEqual(max_active, 4)
        finally:
            release_first_batch.set()
            release_all.set()

        worker.join(timeout=3)

        self.assertFalse(worker.is_alive())
        self.assertEqual(task.status, "completed")
        self.assertCountEqual(
            started,
            ["skill-1", "skill-2", "skill-3", "skill-4", "skill-5"],
        )



    def test_partial_success_preserves_completed_results(self):
        from core.execution_router import ExecutionRouter

        class Backend:
            def execute(self, step, task_id):
                if step["skill"] == "skill-b":
                    raise RuntimeError("skill-b failed")
                return {"status": "completed", "task_id": task_id, "text": step["skill"]}

        router = ExecutionRouter()
        router.register("test", Backend())

        plan = Plan(
            request_id="req_partial",
            skills=["skill-a", "skill-b"],
            steps=[
                {"step": 1, "skill": "skill-a", "backend": "test", "status": "pending"},
                {"step": 2, "skill": "skill-b", "backend": "test", "status": "pending"},
            ],
        )
        task = Task(task_id="task_partial", request_id="req_partial", plan=plan)

        result = Executor(execution_router=router).execute(task)

        self.assertEqual(result.status, "partial_success")
        self.assertIn("skill-a", result.text)
        self.assertTrue(result.warnings)
        self.assertEqual(task.status, "partial_success")


if __name__ == "__main__":
    unittest.main()
