from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .executor import Executor
from .skill_executor import SkillExecutor
from .execution_router import ExecutionRouter
from .local_backend import LocalBackend
from .openai_backend import OpenAIBackend
from .execution_trace import ExecutionTrace
from .models import Request, Plan, Task, Result
from .planner import Planner
from .skill_registry import SkillRegistry


class Runtime:
    def __init__(
        self,
        root: str | Path,
        skill_executor: SkillExecutor | None = None,
        execution_router: ExecutionRouter | None = None,
        openai_runner=None,
        execution_trace=None,
    ):
        self.root = Path(root)
        self.registry = SkillRegistry(self.root)
        self.planner = Planner(self.registry)
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

        self.executor = Executor(
            self.skill_executor,
            self.execution_router,
            execution_trace=self.execution_trace,
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

        decision = self.planner.plan(request.text)
        plan = self._build_plan(request.request_id, decision)

        task_id = self._task_id()
        self._request_texts[task_id] = request.text

        task = Task(
            task_id=task_id,
            request_id=request.request_id,
            project_id=project_id,
            status="pending",
            plan=plan,
        )

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

    @staticmethod
    def _build_plan(request_id, decision):
        steps = [
            {
                "step": index,
                "skill": skill_id,
                "status": "pending",
            }
            for index, skill_id in enumerate(decision.skills, start=1)
        ]

        return Plan(
            request_id=request_id,
            skills=decision.skills,
            steps=steps,
        )

    @staticmethod
    def _request_id() -> str:
        return f"req_{uuid4().hex[:12]}"

    @staticmethod
    def _task_id() -> str:
        return f"task_{uuid4().hex[:12]}"
