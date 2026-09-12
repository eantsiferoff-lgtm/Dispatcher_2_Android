from __future__ import annotations

from collections.abc import Callable
from typing import Any


SkillHandler = Callable[[dict[str, Any], str], dict[str, Any]]


class SkillExecutor:
    def __init__(self):
        self._handlers: dict[str, SkillHandler] = {}

    def register(self, skill_id: str, handler: SkillHandler) -> None:
        if not skill_id:
            raise ValueError("skill_id must not be empty")

        if not callable(handler):
            raise TypeError("handler must be callable")

        self._handlers[skill_id] = handler

    def has_handler(self, skill_id: str) -> bool:
        return skill_id in self._handlers

    def handler_ids(self) -> list[str]:
        return list(self._handlers.keys())


    def execute(
        self,
        step: dict[str, Any],
        task_id: str,
    ) -> dict[str, Any]:
        skill_id = step.get("skill")

        if not skill_id:
            raise ValueError("Step does not contain skill")

        handler = self._handlers.get(skill_id)

        if handler is None:
            raise KeyError(f"No handler registered for skill: {skill_id}")

        return handler(step, task_id)
