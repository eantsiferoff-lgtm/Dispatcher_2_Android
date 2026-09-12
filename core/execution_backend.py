from __future__ import annotations

from .models import Result, Task


class ExecutionBackend:
    def execute(self, task: Task) -> Result:
        return Result(
            task_id=task.task_id,
            status="planned",
            text="Task is ready for backend execution.",
        )
