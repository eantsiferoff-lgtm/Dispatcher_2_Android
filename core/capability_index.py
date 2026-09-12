from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .skill_registry import SkillRecord, SkillRegistry


@dataclass
class Capability:
    skill_id: str
    text: str


class CapabilityIndex:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self._items: list[Capability] = []

    def build(self) -> list[Capability]:
        self._items = [
            Capability(
                skill_id=skill.skill_id,
                text=self._build_text(skill),
            )
            for skill in self.registry.domain()
        ]
        return list(self._items)

    def _build_text(self, skill: SkillRecord) -> str:
        parts = [skill.name, skill.description, skill.metadata.get("role", "")]
        parts.extend(skill.capabilities)
        parts.extend(skill.triggers)
        return " ".join(str(part).strip() for part in parts if str(part).strip())

    def all(self) -> list[Capability]:
        if not self._items:
            self.build()
        return list(self._items)

    def for_skills(self, skill_ids: Iterable[str]) -> list[Capability]:
        wanted = set(skill_ids)
        return [item for item in self.all() if item.skill_id in wanted]
