from __future__ import annotations

from typing import Any

from .models import Result


class ResultAggregator:
    def normalize(self, skill: str, result: Result) -> dict[str, Any]:
        return {
            "skill": skill,
            "status": result.status,
            "data": result.text,
            "metadata": {
                "task_id": result.task_id,
                "artifacts": list(result.artifacts),
                "sources": list(result.sources),
                "warnings": list(result.warnings),
            },
        }

    def aggregate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        statuses = [item.get("status") for item in results]

        if not results:
            status = "empty"
        elif all(item == "completed" for item in statuses):
            status = "completed"
        elif any(item in {"failed", "partial_success"} for item in statuses):
            status = "partial_success"
        else:
            status = "completed"

        return {
            "status": status,
            "data": [item.get("data") for item in results],
            "results": list(results),
        }
