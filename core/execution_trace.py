from __future__ import annotations

from typing import Any


class ExecutionTrace:
    def __init__(self):
        self._events: list[dict[str, Any]] = []

    def record(
        self,
        *,
        request_id: str,
        task_id: str,
        step: int,
        skill: str,
        backend: str | None,
        status: str,
        duration_ms: float,
        error: str | None = None,
        event_type: str = "completed",
        skills: list[str] | None = None,
        confidence: float | None = None,
        workflow_id: str | None = None,
        steps: list[dict[str, Any]] | None = None,
    ) -> None:
        self._events.append({
            "request_id": request_id,
            "task_id": task_id,
            "step": step,
            "skill": skill,
            "backend": backend,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            "event_type": event_type,
            "skills": skills,
            "confidence": confidence,
            "workflow_id": workflow_id,
            "steps": steps,
        })

    def events(self) -> list[dict[str, Any]]:
        return list(self._events)
