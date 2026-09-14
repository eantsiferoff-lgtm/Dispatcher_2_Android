from __future__ import annotations

from typing import Any


class N8NBackend:
    priority = 30

    def __init__(self, client: Any | None = None):
        self.client = client

    def available(self) -> bool:
        return self.client is not None

    def can_execute(self, target: Any) -> bool:
        if not isinstance(target, dict):
            return False

        return (
            bool(target.get("skill"))
            and bool(target.get("workflow"))
            and self.available()
        )

    def execute(self, step: dict[str, Any], task_id: str) -> dict[str, Any]:
        if self.client is None:
            raise RuntimeError("N8N backend is not configured")

        result = self.client.execute(
            step["workflow"],
            payload=step.get("payload"),
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
