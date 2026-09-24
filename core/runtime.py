from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from .executor import Executor
from .skill_executor import SkillExecutor
from .execution_router import ExecutionRouter
from .local_backend import LocalBackend
from .openai_backend import OpenAIBackend
from .n8n_backend import N8NBackend
from .n8n_client import N8NClient
from .execution_trace import ExecutionTrace
from .models import Request, Plan, Task, Result
from .planner import Planner
from .plan_builder import PlanBuilder
from .skill_registry import SkillRegistry
from .skill_lifecycle import SkillLifecycleManager
from .skill_lifecycle_store import JsonSkillLifecycleStore
from .config import DispatcherConfig
from .data_paths import DataPaths


class Runtime:
    def __init__(
        self,
        root: str | Path,
        data_root: str | Path | None = None,
        skill_executor: SkillExecutor | None = None,
        execution_router: ExecutionRouter | None = None,
        openai_runner=None,
        execution_trace=None,
        auto_refresh_lifecycle: bool = True,
    ):
        self.root = Path(root)
        configured_data_root = os.getenv("DISPATCHER_DATA_DIR")
        self.data_root = Path(data_root or configured_data_root or self.root)
        self.data_paths = DataPaths(self.data_root)
        self.config = DispatcherConfig.from_file(self.root / "dispatcher.yaml")
        self.lifecycle_store = JsonSkillLifecycleStore(self.data_paths.state / "skill_lifecycle.json")
        self.registry = SkillRegistry(self.root, lifecycle_store=self.lifecycle_store)
        self.lifecycle = SkillLifecycleManager(store=self.lifecycle_store)
        self.auto_refresh_lifecycle = auto_refresh_lifecycle
        if self.auto_refresh_lifecycle:
            self.registry.refresh_lifecycle(self.lifecycle)
        self.planner = Planner(self.registry)
        self.plan_builder = PlanBuilder(registry=self.registry)
        self.skill_executor = skill_executor or SkillExecutor()
        self.execution_router = execution_router or ExecutionRouter()
        self._request_texts = {}
        self.execution_trace = execution_trace or ExecutionTrace()

        if self.execution_router.select("local") is None:
            self.execution_router.register(
                "local",
                LocalBackend(self.skill_executor),
            )
        if openai_runner is not None and self.execution_router.select("openai") is None:
            self.execution_router.register(
                "openai",
                OpenAIBackend(
                    agent_runner=openai_runner,
                    request_provider=lambda task_id: self._request_texts[task_id],
                ),
            )
        n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
        if n8n_webhook_url and self.execution_router.select("n8n") is None:
            self.execution_router.register(
                "n8n",
                N8NBackend(client=N8NClient(n8n_webhook_url)),
            )

        self.executor = Executor(
            self.skill_executor,
            self.execution_router,
            execution_trace=self.execution_trace,
            lifecycle=self.lifecycle,
            registry=self.registry,
            max_parallel_skills=self.config.max_parallel_skills,
        )
    def prepare(
        self,
        text: str,
        attachments: list[str] | None = None,
        project_id: str | None = None,
    ):
        request = Request(
            request_id=self._request_id(),
            text=text,
            attachments=attachments or [],
            project_id=project_id,
        )

        if self.execution_trace is not None:
            self.execution_trace.record(request_id=request.request_id, task_id="", step=0, skill="", backend=None, status="received", duration_ms=0.0, event_type="request")
        decision = self.planner.plan(request.text)

        if not decision.workflow_id:
            decision.workflow_id = self._select_workflow(decision)

        if self.execution_trace is not None:
            self.execution_trace.record(request_id=request.request_id, task_id="", step=0, skill="", backend=None, status="selected", duration_ms=0.0, event_type="planner_decision", skills=list(decision.skills), confidence=decision.confidence, workflow_id=decision.workflow_id)

        workflow = self._workflow_metadata(decision.workflow_id)

        plan = self.plan_builder.build(
            request.request_id,
            decision,
            workflow=workflow,
        )

        task_id = self._task_id()
        self._request_texts[task_id] = request.text

        task = Task(
            task_id=task_id,
            request_id=request.request_id,
            project_id=project_id,
            status="pending",
            plan=plan,
        )

        if self.execution_trace is not None:
            self.execution_trace.record(request_id=request.request_id, task_id=task_id, step=0, skill="", backend=None, status="built", duration_ms=0.0, event_type="plan_built", skills=list(plan.skills), steps=list(plan.steps))
            self.execution_trace.record(request_id=request.request_id, task_id=task_id, step=0, skill="", backend=None, status=task.status, duration_ms=0.0, event_type="task_created")
        return request, plan, task

    def run(
        self,
        text: str,
        attachments: list[str] | None = None,
        project_id: str | None = None,
    ) -> tuple[Request, Plan, Task, Result]:
        request, plan, task = self.prepare(
            text=text,
            attachments=attachments,
            project_id=project_id,
        )

        result = self.executor.execute(task)
        return request, plan, task, result

    def _select_workflow(self, decision) -> str | None:
        selected_skills = set(decision.skills)

        if not selected_skills:
            return None

        matches = []

        for workflow_id, workflow in self.config.workflows.items():
            workflow_skills = {
                step["skill"]
                for step in workflow.get("steps", [])
                if step.get("skill")
            }

            if workflow_skills == selected_skills:
                matches.append(workflow_id)

        if len(matches) == 1:
            return matches[0]

        return None

    def _workflow_metadata(
        self,
        workflow_id: str | None,
    ) -> dict[str, dict]:
        if not workflow_id:
            return {}

        workflow = self.config.workflows.get(workflow_id)
        if not workflow:
            return {}

        return {
            step["skill"]: {
                "depends_on": list(step.get("depends_on", [])),
                "execution_mode": step.get("execution_mode", "ordered"),
                "backend": step.get("backend"),
                "workflow": step.get("workflow"),
            }
            for step in workflow.get("steps", [])
            if step.get("skill")
        }

    @staticmethod
    def _request_id() -> str:
        return f"req_{uuid4().hex[:12]}"

    @staticmethod
    def _task_id() -> str:
        return f"task_{uuid4().hex[:12]}"
