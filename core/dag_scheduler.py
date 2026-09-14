from __future__ import annotations


class DAGScheduler:
    def __init__(self, max_parallel_skills: int = 4):
        if max_parallel_skills < 1:
            raise ValueError("max_parallel_skills must be >= 1")
        self.max_parallel_skills = max_parallel_skills

    def ready_steps(self, steps: list[dict]) -> list[dict]:
        completed = {
            step.get("step")
            for step in steps
            if step.get("status") == "completed"
        }

        running_count = sum(
            1
            for step in steps
            if step.get("status") == "running"
        )
        available_capacity = max(
            0,
            self.max_parallel_skills - running_count,
        )

        if available_capacity == 0:
            return []

        ready = []

        for step in steps:
            if step.get("status") != "pending":
                continue

            dependencies = step.get("depends_on", []) or []

            if all(dependency in completed for dependency in dependencies):
                ready.append(step)

            if len(ready) >= available_capacity:
                break

        return ready
