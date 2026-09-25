from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Plan, Task


class TaskStateStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, task_id: str) -> Path:
        return self.root / f"{task_id}.json"

    def save(self, task: Task) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(task.task_id).write_text(
            json.dumps(asdict(task), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, task_id: str) -> Task | None:
        path = self._path(task_id)
        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        plan_data = data.get("plan")

        plan = None
        if plan_data is not None:
            plan = Plan(**plan_data)

        data["plan"] = plan
        return Task(**data)
