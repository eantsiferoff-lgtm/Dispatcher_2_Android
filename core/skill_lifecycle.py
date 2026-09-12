from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .skill_lifecycle_store import SkillLifecycleStore


ACTIVE = "active"
DORMANT = "dormant"
ARCHIVED = "archived"


@dataclass(frozen=True)
class LifecycleConfig:
    dormant_after_days: int = 180
    archive_after_days: int = 365


class SkillLifecycleManager:
    def __init__(self, config: LifecycleConfig | None = None, store: SkillLifecycleStore | None = None):
        self.config = config or LifecycleConfig()
        self.store = store

    def status(self, metadata: dict[str, Any], *, now: datetime | None = None) -> str:
        lifecycle = metadata.get("lifecycle") or {}
        last_used_at = lifecycle.get("last_used_at")

        if not last_used_at:
            return ACTIVE

        last_used = self._parse_datetime(last_used_at)
        current = now or datetime.now(timezone.utc)
        age_days = (current - last_used).total_seconds() / 86400

        if age_days >= self.config.archive_after_days:
            return ARCHIVED
        if age_days >= self.config.dormant_after_days:
            return DORMANT
        return ACTIVE

    def record_usage(self, metadata: dict[str, Any], *, skill_id: str | None = None, now: datetime | None = None) -> None:
        lifecycle = metadata.setdefault("lifecycle", {})
        lifecycle["status"] = ACTIVE
        lifecycle["last_used_at"] = (now or datetime.now(timezone.utc)).isoformat()
        lifecycle["usage_count"] = int(lifecycle.get("usage_count", 0)) + 1

        if self.store is not None and skill_id:
            self.store.save(skill_id, lifecycle)

    def restore(self, metadata: dict[str, Any], *, skill_id: str | None = None, now: datetime | None = None) -> None:
        lifecycle = metadata.setdefault("lifecycle", {})
        lifecycle["status"] = ACTIVE
        lifecycle["last_used_at"] = (now or datetime.now(timezone.utc)).isoformat()
        lifecycle["restored_count"] = int(lifecycle.get("restored_count", 0)) + 1

        if self.store is not None and skill_id:
            self.store.save(skill_id, lifecycle)

    def refresh(self, skill_id: str, metadata: dict[str, Any], *, now: datetime | None = None) -> str:
        lifecycle = metadata.get("lifecycle") or {}
        if not lifecycle.get("last_used_at"):
            return ACTIVE

        status = self.status(metadata, now=now)
        lifecycle = metadata.setdefault("lifecycle", {})
        lifecycle["status"] = status
        if self.store is not None:
            self.store.save(skill_id, lifecycle)
        return status

    @staticmethod
    def _parse_datetime(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
