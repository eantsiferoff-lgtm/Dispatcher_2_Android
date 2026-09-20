from __future__ import annotations

from typing import Any

from core.models import Plan
from core.planner import PlannerDecision


class PlanBuilder:
    def build(
        self,
        request_id: str,
        decision: PlannerDecision,
        workflow: dict[str, dict[str, Any]] | None = None,
    ) -> Plan:
        steps = []

        for index, skill_id in enumerate(decision.skills, start=1):
            if workflow and skill_id in workflow:
                metadata = workflow[skill_id]
                depends_on = list(metadata.get("depends_on", []))
                execution_mode = metadata.get("execution_mode", "ordered")
                backend = metadata.get("backend")
                tool_slug = metadata.get("tool_slug")
                workflow_name = metadata.get("workflow")
            else:
                depends_on = [] if index == 1 else [index - 1]
                execution_mode = "ordered"
                backend = None
                tool_slug = None
                workflow_name = None

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
