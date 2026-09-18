from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .skill_registry import SkillRegistry


class RoutingEngine:
    def __init__(self, routing_path: str | Path, registry: SkillRegistry):
        self.routing_path = Path(routing_path)
        self.registry = registry
        if self.routing_path.exists():
            data = yaml.safe_load(self.routing_path.read_text(encoding="utf-8")) or {}
        else:
            data = {}
        self.rules: list[dict[str, Any]] = list(data.get("rules") or [])

    @staticmethod
    def _normalize(text: str) -> str:
        return text.lower().replace("ё", "е")

    def route(self, request: str) -> list[str]:
        text = self._normalize(request)
        result: list[str] = []
        for rule in self.rules:
            signals = rule.get("when") or []
            matched = any(self._normalize(str(signal)) in text for signal in signals)
            if not matched:
                continue
            for skill_id in rule.get("skills") or []:
                skill = self.registry.get(skill_id)
                if skill is None or not self.registry.is_eligible(skill):
                    continue
                if skill_id not in result:
                    result.append(skill_id)
        return result
