from __future__ import annotations

from typing import Any, Callable

from .skill_registry import SkillRegistry


class AIPlanner:
    def __init__(self, registry: SkillRegistry, runner: Callable[[str], Any]):
        self.registry = registry
        self.runner = runner

    def plan(self, request: str) -> list[str]:
        result = self.runner(request)
        if result is None:
            return []
        if isinstance(result, str):
            skill_ids = [item.strip() for item in result.split(",") if item.strip()]
        else:
            skill_ids = list(result)
        allowed = {skill.skill_id for skill in self.registry.active_domain()}
        return [skill_id for skill_id in skill_ids if skill_id in allowed]
