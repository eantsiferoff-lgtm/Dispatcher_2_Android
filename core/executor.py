from __future__ import annotations

from .models import Result, Task
from .skill_executor import SkillExecutor
from .execution_router import ExecutionRouter
from .security_policy import SecurityPolicy
from .execution_trace import ExecutionTrace
from .skill_lifecycle import SkillLifecycleManager
from .skill_registry import SkillRegistry
import time


class Executor:
    def __init__(self, skill_executor: SkillExecutor | None = None, execution_router: ExecutionRouter | None = None, security_policy: SecurityPolicy | None = None, execution_trace: ExecutionTrace | None = None, lifecycle: SkillLifecycleManager | None = None, registry: SkillRegistry | None = None):
        self.skill_executor = skill_executor or SkillExecutor()
        self.execution_router = execution_router
        self.security_policy = security_policy or SecurityPolicy()
        self.execution_trace = execution_trace
        self.lifecycle = lifecycle or SkillLifecycleManager()
        self.registry = registry

    def _execute_step(self, step: dict, task: Task):
        step["status"] = "running"
        step_started = time.perf_counter()

        action = step.get("action")
        if action:
            policy_result = self.security_policy.check(action)
            if policy_result != "SAFE":
                raise RuntimeError(
                    f"Security policy: {policy_result} for action: {action}"
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
                step = task.plan.steps[index]
                task.current_step = index + 1

                if step.get("execution_mode") == "parallel":
                    group = []
                    group_start = index
                    while (
                        index < len(task.plan.steps)
                        and task.plan.steps[index].get("execution_mode") == "parallel"
                    ):
                        group.append(task.plan.steps[index])
                        index += 1

                    parallel_results = self._execute_parallel_steps(group, task)

                    for group_offset, (step_result, _step_started) in enumerate(parallel_results):
                        step_index = group_start + group_offset + 1
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
            task.status = "failed"
            task.errors.append(str(exc))

            if task.plan.steps and task.current_step > 0:
                failed_step = task.plan.steps[task.current_step - 1]
                failed_step["status"] = "failed"
                if self.execution_trace is not None:
                    self.execution_trace.record(request_id=task.request_id, task_id=task.task_id, step=task.current_step, skill=failed_step.get("skill", ""), backend=failed_step.get("backend"), status="failed", duration_ms=(time.perf_counter() - step_started) * 1000.0 if "step_started" in locals() else 0.0, error=str(exc))

            return Result(
                task_id=task.task_id,
                status="failed",
                warnings=[str(exc)],
            )
