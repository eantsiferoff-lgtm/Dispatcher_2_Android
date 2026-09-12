from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SkillRecord:
    skill_id: str
    path: str
    name: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def capabilities(self) -> list[str]:
        return list(self.metadata.get("capabilities", []))

    @property
    def triggers(self) -> list[str]:
        return list(self.metadata.get("triggers", []))


class SkillRegistry:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.skills_dir = self.root / "skills"
        self._records = {}

    def discover(self) -> list[SkillRecord]:
        records: list[SkillRecord] = []

        if not self.skills_dir.exists():
            return records

        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            records.append(self._load_skill(skill_file))

        self._validate(records)
        self._records = {record.skill_id: record for record in records}
        return records

    def _load_skill(self, skill_file: Path) -> SkillRecord:
        text = skill_file.read_text(encoding="utf-8")

        if not text.startswith("---"):
            raise ValueError(f"Missing YAML frontmatter: {skill_file}")

        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid frontmatter: {skill_file}")

        frontmatter = yaml.safe_load(parts[1]) or {}

        skill_id = skill_file.parent.name
        name = frontmatter.get("name", skill_id)
        description = str(frontmatter.get("description", "")).strip()
        metadata = frontmatter.get("metadata") or {}

        return SkillRecord(
            skill_id=skill_id,
            path=str(skill_file.relative_to(self.root)),
            name=name,
            description=description,
            metadata=metadata,
        )

    def _validate(self, records: list[SkillRecord]) -> None:
        ids = [record.skill_id for record in records]

        duplicates = {skill_id for skill_id in ids if ids.count(skill_id) > 1}
        if duplicates:
            raise ValueError(
                f"Duplicate skill ids: {', '.join(sorted(duplicates))}"
            )

    def get(self, skill_id: str) -> SkillRecord | None:
        if not self._records:
            self.discover()
        return self._records.get(skill_id)

    def all(self) -> list[SkillRecord]:
        if not self._records:
            self.discover()
        return list(self._records.values())

    def domain(self) -> list[SkillRecord]:
        return [skill for skill in self.all() if skill.metadata.get("role") != "top-level-router"]

    def top_level(self) -> SkillRecord | None:
        for skill in self.all():
            if skill.metadata.get("role") == "top-level-router":
                return skill
        return None
