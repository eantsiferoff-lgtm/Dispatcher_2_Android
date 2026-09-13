from __future__ import annotations

from core.models import Plan
from core.planner import PlannerDecision


class PlanBuilder:
    def build(self, request_id: str, decision: PlannerDecision) -> Plan:
        steps = [
            {
                "step": index,
                "skill": skill_id,
                "status": "pending",
                "depends_on": [] if index == 1 else [index - 1],
                "execution_mode": "ordered",
            }
            for index, skill_id in enumerate(decision.skills, start=1)
        ]

        return Plan(
            request_id=request_id,
            skills=list(decision.skills),
            steps=steps,
        )
