from __future__ import annotations

from typing import Any

from .composio_gateway import ComposioGateway


class ComposioBackend:
    priority = 50

    def __init__(self, session: Any | None = None, gateway: ComposioGateway | None = None):
        self.session = session
        self.gateway = gateway

    def available(self) -> bool:
        return self.session is not None

    def can_execute(self, target: Any) -> bool:
        if not isinstance(target, dict):
            return False

        return (
            bool(target.get("skill"))
            and bool(target.get("tool_slug"))
            and self.available()
        )

    def execute(self, step: dict[str, Any], task_id: str) -> dict[str, Any]:
        if self.session is None:
            raise RuntimeError("Composio backend is not configured")

        result = self.session.execute(
            step["tool_slug"],
            arguments=step.get("arguments"),
            account=step.get("account"),
        )

        if isinstance(result, dict):
            return {
                "status": result.get("status", "completed"),
                "task_id": task_id,
                "text": str(result.get("data", result)),
            }

        return {
            "status": "completed",
            "task_id": task_id,
            "text": str(result),
        }
