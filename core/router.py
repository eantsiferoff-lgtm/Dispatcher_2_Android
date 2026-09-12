from __future__ import annotations

from pathlib import Path

from .runtime import Runtime


class Dispatcher:
    """Backward-compatible facade over the new Runtime."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.runtime = Runtime(self.root)

    def classify(self, request: str):
        return self.runtime.planner.plan(request).skills

    def plan(self, request: str):
        _, plan, _ = self.runtime.prepare(request)
        return {
            "request": request,
            "skills": plan.skills,
            "steps": plan.steps,
        }

    def build_context(self, request: str):
        _, plan, _ = self.runtime.prepare(request)
        instructions = {
            skill_id: self.runtime.registry.get(skill_id)
            for skill_id in plan.skills
        }

        return {
            "plan": {
                "request": request,
                "skills": plan.skills,
                "steps": plan.steps,
            },
            "skill_instructions": instructions,
        }
