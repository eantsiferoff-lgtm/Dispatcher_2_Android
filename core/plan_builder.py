from __future__ import annotations

from typing import Any

from core.models import Plan
from core.planner import PlannerDecision


class PlanBuilder:
    def __init__(self, registry=None):
        self.registry = registry

    def build(
        self,
        request_id: str,
        decision: PlannerDecision,
        workflow: dict[str, dict[str, Any]] | None = None,
    ) -> Plan:
        steps = []

        for index, skill_id in enumerate(decision.skills, start=1):
            skill_metadata = {}

            if self.registry is not None:
                skill = self.registry.get(skill_id)
                if skill is not None:
                    skill_metadata = skill.metadata

            if workflow and skill_id in workflow:
                metadata = workflow[skill_id]

                depends_on = list(metadata.get("depends_on", []))
                execution_mode = metadata.get(
                    "execution_mode",
                    skill_metadata.get("execution_mode", "ordered"),
                )
                backend = metadata.get(
                    "backend",
                    skill_metadata.get("backend"),
                )
                tool_slug = metadata.get("tool_slug")
                workflow_name = metadata.get("workflow")

            else:
                depends_on = [] if index == 1 else [index - 1]
                execution_mode = skill_metadata.get(
                    "execution_mode",
                    "ordered",
                )
                backend = skill_metadata.get("backend")
                tool_slug = skill_metadata.get("tool_slug")
                workflow_name = skill_metadata.get("workflow")

            steps.append(
                {
                    "step": index,
                    "skill": skill_id,
                    "status": "pending",
                    "depends_on": depends_on,
                    "execution_mode": execution_mode,
                    **({"backend": backend} if backend else {}),
                    **({"tool_slug": tool_slug} if tool_slug else {}),
                    **({"workflow": workflow_name} if workflow_name else {}),
                }
            )

        return Plan(
            request_id=request_id,
            skills=list(decision.skills),
            steps=steps,
        )
