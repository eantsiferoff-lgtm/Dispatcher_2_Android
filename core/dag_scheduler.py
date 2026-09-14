from __future__ import annotations


class DAGScheduler:
    def __init__(self, max_parallel_skills: int = 4):
        if max_parallel_skills < 1:
            raise ValueError("max_parallel_skills must be >= 1")
        self.max_parallel_skills = max_parallel_skills

    def validate(self, steps: list[dict]) -> None:
        step_ids = {
            step.get("step")
            for step in steps
            if step.get("step") is not None
        }

        dependencies = {
            step.get("step"): list(step.get("depends_on", []) or [])
            for step in steps
        }

        dependencies = {
            step.get("step"): list(step.get("depends_on", []) or [])
            for step in steps
        }

        for step in steps:
            for dependency in step.get("depends_on", []) or []:
                if dependency not in step_ids:
                    raise ValueError(
                        f"Unknown dependency: step {step.get('step')} -> {dependency}"
                    )

        visiting = set()
        visited = set()

        def visit(step_id):
            if step_id in visiting:
                raise ValueError(f"Cyclic dependency detected at step {step_id}")
            if step_id in visited:
                return

            visiting.add(step_id)
            for dependency in dependencies.get(step_id, []):
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in dependencies:
            visit(step_id)

        visiting = set()
        visited = set()

        def visit(step_id):
            if step_id in visiting:
                raise ValueError(f"Cyclic dependency detected at step {step_id}")
            if step_id in visited:
                return

            visiting.add(step_id)
            for dependency in dependencies.get(step_id, []):
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in dependencies:
            visit(step_id)

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
