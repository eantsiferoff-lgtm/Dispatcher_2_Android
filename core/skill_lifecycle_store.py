from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SkillLifecycleStore:
    def load(self, skill_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def save(self, skill_id: str, state: dict[str, Any]) -> None:
        raise NotImplementedError


class JsonSkillLifecycleStore(SkillLifecycleStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load_all(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}

        text = self.path.read_text(encoding="utf-8").strip()
        if not text:
            return {}

        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Lifecycle state must be a JSON object")

        return data

    def load(self, skill_id: str) -> dict[str, Any]:
        return dict(self._load_all().get(skill_id, {}))

    def save(self, skill_id: str, state: dict[str, Any]) -> None:
        data = self._load_all()
        data[skill_id] = dict(state)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
