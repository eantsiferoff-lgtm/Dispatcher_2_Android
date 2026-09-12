from __future__ import annotations
from typing import Any

class ExecutionRouter:
    def __init__(self):
        self._backends: dict[str, Any] = {}

    def register(self, name: str, backend: Any) -> None:
        if not name:
            raise ValueError("backend name must not be empty")
        if backend is None:
            raise ValueError("backend must not be None")
        self._backends[name] = backend

    def select(self, name: str) -> Any | None:
        return self._backends.get(name)

    def select_available(self) -> Any | None:
        available = []
        for backend in self._backends.values():
            check = getattr(backend, "available", None)
            if callable(check) and not check():
                continue
            available.append(backend)

        if not available:
            return None

        return max(available, key=lambda backend: getattr(backend, "priority", 0))

    def route(self, task: Any) -> str | None:
        candidates = []

        for name, backend in self._backends.items():
            check_available = getattr(backend, "available", None)
            if callable(check_available) and not check_available():
                continue

            check_task = getattr(backend, "can_execute", None)
            if callable(check_task) and not check_task(task):
                continue

            candidates.append((name, backend))

        if not candidates:
            return None

        name, _ = max(
            candidates,
            key=lambda item: getattr(item[1], "priority", 0),
        )
        return name

    def execute(self, name: str, step: dict, task_id: str | None = None) -> Any:
        backend = self.select(name)
        if backend is None:
            raise KeyError(f"No backend registered: {name}")
        if task_id is None:
            return backend.execute(step)
        return backend.execute(step, task_id)
