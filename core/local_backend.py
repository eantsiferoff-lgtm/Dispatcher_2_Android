from __future__ import annotations

from typing import Any, Callable

from .skill_executor import SkillExecutor


class LocalBackend:
    priority = 100

    def __init__(self, skill_executor: SkillExecutor | None = None):
        self.skill_executor = skill_executor or SkillExecutor()

    def available(self) -> bool:
        return True

    def can_execute(self, target: Any) -> bool:
        if isinstance(target, dict):
            skill_id = target.get("skill")
            return bool(skill_id) and self.skill_executor.has_handler(skill_id)
        plan = getattr(target, "plan", None)
        if plan is None or not plan.skills:
            return False
        return all(self.skill_executor.has_handler(skill_id) for skill_id in plan.skills)

    def register(self, skill_id: str, handler: Callable[..., Any]) -> None:
        self.skill_executor.register(skill_id, handler)

    def execute(self, step: dict[str, Any], task_id: str) -> dict[str, Any]:
        return self.skill_executor.execute(step, task_id)
