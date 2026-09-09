from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Request:
    request_id: str
    text: str
    attachments: list[str] = field(default_factory=list)
    project_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    request_id: str
    skills: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    requires_confirmation: bool = False


@dataclass
class Task:
    task_id: str
    request_id: str
    project_id: str | None = None
    status: str = "pending"
    current_step: int = 0
    plan: Plan | None = None
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Result:
    task_id: str
    status: str
    text: str = ""
    artifacts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
