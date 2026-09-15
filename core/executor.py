from __future__ import annotations

from .models import Result, Task
from .skill_executor import SkillExecutor
from .execution_router import ExecutionRouter
from .security_policy import SecurityPolicy
from .confirmation_engine import ConfirmationEngine
from .execution_trace import ExecutionTrace
from .skill_lifecycle import SkillLifecycleManager
from .skill_registry import SkillRegistry
from .dag_scheduler import DAGScheduler
import time


class Executor:
    def __init__(self, skill_executor: SkillExecutor | None = None, execution_router: ExecutionRouter | None = None, security_policy: SecurityPolicy | None = None, confirmation_engine: ConfirmationEngine | None = None, execution_trace: ExecutionTrace | None = None, lifecycle: SkillLifecycleManager | None = None, registry: SkillRegistry | None = None, max_parallel_skills: int = 4):
        self.skill_executor = skill_executor or SkillExecutor()
        self.execution_router = execution_router
        self.security_policy = security_policy or SecurityPolicy()
        self.confirmation_engine = confirmation_engine or ConfirmationEngine(self.security_policy)
        self.execution_trace = execution_trace
        self.lifecycle = lifecycle or SkillLifecycleManager()
        self.registry = registry
        self.max_parallel_skills = max_parallel_skills
        self.dag_scheduler = DAGScheduler(max_parallel_skills=max_parallel_skills)

    def _execute_step(self, step: dict, task: Task):
        step["status"] = "running"
        step_started = time.perf_counter()

        if self.execution_trace is not None:
            self.execution_trace.record(
                request_id=task.request_id,
                task_id=task.task_id,
                step=step.get("step", 0),
                skill=step.get("skill", ""),
                backend=step.get("backend"),
                status="running",
                duration_ms=0.0,
                event_type="started",
            )

        action = step.get("action")
        if action:
            confirmation = self.confirmation_engine.check(step)
            if confirmation["status"] == "confirmation_required":
                step["status"] = "confirmation_required"
                return confirmation, step_started
            if confirmation["status"] == "denied":
                raise RuntimeError(
                    f"Security policy: DENY for action: {action}"
                )

        backend_name = step.get("backend")

        if not backend_name and self.execution_router is not None:
            backend_name = self.execution_router.route(step)
            if backend_name:
                step["backend"] = backend_name

        if backend_name:
            if self.execution_router is None:
                raise RuntimeError(
                    "ExecutionRouter is required for backend execution"
                )
            step_result = self.execution_router.execute(
                backend_name,
                step,
                task.task_id,
            )
        else:
            step_result = self.skill_executor.execute(
                step,
                task.task_id,
            )

        if isinstance(step_result, dict):
            step["result"] = step_result

        step["status"] = "completed"

        skill_id = step.get("skill")
        if self.registry is not None and skill_id:
            skill = self.registry.get(skill_id)
            if skill is not None:
                self.lifecycle.record_usage(
                    skill.metadata,
                    skill_id=skill_id,
                )

        if self.execution_trace is not None:
            self.execution_trace.record(
                request_id=task.request_id,
                task_id=task.task_id,
                step=step.get("step", 0),
                skill=step.get("skill", ""),
                backend=step.get("backend"),
                status="completed",
                duration_ms=(time.perf_counter() - step_started) * 1000.0,
            )

        return step_result, step_started

    def _execute_parallel_steps(self, steps: list[dict], task: Task):
        from concurrent.futures import ThreadPoolExecutor

        results = [None] * len(steps)

        with ThreadPoolExecutor(max_workers=len(steps)) as pool:
            futures = [
                pool.submit(self._execute_step, step, task)
                for step in steps
            ]

            for index, future in enumerate(futures):
                results[index] = future.result()

        return results

    def execute(self, task: Task) -> Result:
        if task.plan is None:
            task.status = "failed"
            task.errors.append("Task has no plan")
            return Result(
                task_id=task.task_id,
                status="failed",
                warnings=["Task has no plan"],
            )

        task.status = "running"
        task.current_step = 0
        task.errors.clear()
        result_text = ""
        result_artifacts = []
        result_sources = []
        result_warnings = []

        try:
            index = 0
            while index < len(task.plan.steps):
                ready_steps = self.dag_scheduler.ready_steps(task.plan.steps)

                if not ready_steps:
                    pending_steps = [
                        step
                        for step in task.plan.steps
                        if step.get("status") == "pending"
                    ]
                    if pending_steps:
                        raise RuntimeError("No executable DAG steps are ready")
                    break

                step = ready_steps[0]
                index = task.plan.steps.index(step)
                task.current_step = index + 1

                if step.get("execution_mode") == "parallel":
                    group = [
                        ready_step
                        for ready_step in ready_steps
                        if ready_step.get("execution_mode") == "parallel"
                    ]

                    if not group:
                        group = [step]

                    parallel_results = self._execute_parallel_steps(group, task)

                    for group_step, (step_result, _step_started) in zip(group, parallel_results):
                        step_index = task.plan.steps.index(group_step) + 1
                        if isinstance(step_result, dict) and step_result.get("status") == "confirmation_required":
                            task.status = "confirmation_required"
                            return Result(task_id=task.task_id, status="confirmation_required", warnings=["Security policy: CONFIRM for action: " + str(step_result.get("action", ""))])
                        if isinstance(step_result, dict):
                            if step_result.get("text") is not None:
                                result_text = str(step_result["text"])
                            result_artifacts.extend(step_result.get("artifacts", []))
                            result_sources.extend(step_result.get("sources", []))
                            result_warnings.extend(step_result.get("warnings", []))

                            if step_index < len(task.plan.steps):
                                task.plan.steps[step_index]["input"] = step_result.get("text", "")
                else:
                    step_result, _step_started = self._execute_step(step, task)
                    if isinstance(step_result, dict) and step_result.get("status") == "confirmation_required":
                        task.status = "confirmation_required"
                        return Result(task_id=task.task_id, status="confirmation_required", warnings=["Security policy: CONFIRM for action: " + str(step_result.get("action", ""))])
                    index += 1

                    if isinstance(step_result, dict):
                        if step_result.get("text") is not None:
                            result_text = str(step_result["text"])
                        result_artifacts.extend(step_result.get("artifacts", []))
                        result_sources.extend(step_result.get("sources", []))
                        result_warnings.extend(step_result.get("warnings", []))

                        if index < len(task.plan.steps):
                            task.plan.steps[index]["input"] = step_result.get("text", "")

            task.status = "completed"

            return Result(
                task_id=task.task_id,
                status="completed",
                text=result_text,
                artifacts=result_artifacts,
                sources=result_sources,
                warnings=result_warnings,
            )

        except Exception as exc:
            task.status = "partial_success" if result_text or result_artifacts or result_sources else "failed"
            task.errors.append(str(exc))

            if task.plan.steps and task.current_step > 0:
                failed_step = task.plan.steps[task.current_step - 1]
                failed_step["status"] = "failed"
                if self.execution_trace is not None:
                    self.execution_trace.record(request_id=task.request_id, task_id=task.task_id, step=task.current_step, skill=failed_step.get("skill", ""), backend=failed_step.get("backend"), status="failed", duration_ms=(time.perf_counter() - step_started) * 1000.0 if "step_started" in locals() else 0.0, error=str(exc), event_type="failed")

            return Result(
                task_id=task.task_id,
                status=task.status,
                text=result_text,
                artifacts=result_artifacts,
                sources=result_sources,
                warnings=result_warnings + [str(exc)],
            )
