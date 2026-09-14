from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DispatcherConfig:
    registry_path: str
    routing_path: str
    allow_multi_skill: bool
    max_parallel_skills: int
    prefer_specific_skill: bool
    preserve_project_context: bool
    verification_required: bool
    check_conflicts: bool
    distinguish_facts_calculations_assumptions: bool
    workflows: dict[str, dict[str, Any]]

    @classmethod
    def from_file(cls, path: str | Path) -> "DispatcherConfig":
        config_path = Path(path)
        if not config_path.exists():
            data: dict[str, Any] = {
                "registry": "registry.yaml",
                "routing": "routing.yaml",
                "orchestration": {
                    "allow_multi_skill": True,
                    "max_parallel_skills": 4,
                    "prefer_specific_skill": True,
                    "preserve_project_context": True,
                },
                "verification": {
                    "required": True,
                    "check_conflicts": True,
                    "distinguish_facts_calculations_assumptions": True,
                },
            }
        else:
            data = yaml.safe_load(
                config_path.read_text(encoding="utf-8")
            ) or {}

        orchestration = data.get("orchestration") or {}
        verification = data.get("verification") or {}

        max_parallel_skills = int(orchestration.get("max_parallel_skills", 1))
        if max_parallel_skills < 1:
            raise ValueError("max_parallel_skills must be >= 1")

        return cls(
            registry_path=str(data.get("registry", "registry.yaml")),
            routing_path=str(data.get("routing", "routing.yaml")),
            allow_multi_skill=bool(orchestration.get("allow_multi_skill", False)),
            max_parallel_skills=max_parallel_skills,
            prefer_specific_skill=bool(
                orchestration.get("prefer_specific_skill", True)
            ),
            preserve_project_context=bool(
                orchestration.get("preserve_project_context", True)
            ),
            verification_required=bool(verification.get("required", True)),
            check_conflicts=bool(verification.get("check_conflicts", True)),
            workflows=dict(data.get("workflows") or {}),
            distinguish_facts_calculations_assumptions=bool(
                verification.get(
                    "distinguish_facts_calculations_assumptions",
                    True,
                )
            ),
        )
