from __future__ import annotations

from typing import Any

from .models import Result


class VerificationLayer:
    CHECK_TYPES = {
        "FACT",
        "CALCULATION",
        "ASSUMPTION",
        "CONFLICT",
        "WARNING",
    }

    def verify(self, result: Result) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []

        for warning in result.warnings:
            checks.append({
                "type": "WARNING",
                "message": str(warning),
                "severity": "warning",
            })

        return {
            "status": "verified",
            "checks": checks,
        }
