from __future__ import annotations

from .models import Result, Task
from .skill_executor import SkillExecutor
from .execution_router import ExecutionRouter
from .security_policy import SecurityPolicy
from .execution_trace import ExecutionTrace
import time


class Executor:
    def __init__(self, skill_executor: SkillExecutor | None = None, execution_router: ExecutionRouter | None = None, security_policy: SecurityPolicy | None = None, execution_trace: ExecutionTrace | None = None):
        self.skill_executor = skill_executor or SkillExecutor()
        self.execution_router = execution_router
        self.security_policy = security_policy or SecurityPolicy()
        self.execution_trace = execution_trace

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
            for index, step in enumerate(task.plan.steps, start=1):
                step["status"] = "running"
                task.current_step = index
                step_started = time.perf_counter()

                action = step.get("action")
                if action:
                    policy_result = self.security_policy.check(action)
                    if policy_result != "SAFE":
                        raise RuntimeError(f"Security policy: {policy_result} for action: {action}")

                backend_name = step.get("backend")

                if not backend_name and self.execution_router is not None:
                    backend_name = self.execution_router.route(step)
                    if backend_name:
                        step["backend"] = backend_name

                if backend_name:
                    if self.execution_router is None:
                        raise RuntimeError("ExecutionRouter is required for backend execution")
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
                    if step_result.get("text") is not None:
                        result_text = str(step_result["text"])
                    result_artifacts.extend(step_result.get("artifacts", []))
                    result_sources.extend(step_result.get("sources", []))
                    result_warnings.extend(step_result.get("warnings", []))
                    step["result"] = step_result
                    if index < len(task.plan.steps):
                        task.plan.steps[index]["input"] = step_result.get("text", "")

                step["status"] = "completed"
                if self.execution_trace is not None:
                    self.execution_trace.record(request_id=task.request_id, task_id=task.task_id, step=index, skill=step.get("skill", ""), backend=step.get("backend"), status="completed", duration_ms=(time.perf_counter() - step_started) * 1000.0)

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
