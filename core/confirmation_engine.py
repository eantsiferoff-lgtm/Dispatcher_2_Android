from __future__ import annotations

from typing import Any

from .security_policy import SecurityPolicy


class ConfirmationEngine:
    def __init__(self, security_policy: SecurityPolicy | None = None):
        self.security_policy = security_policy or SecurityPolicy()

    def check(self, step: dict[str, Any]) -> dict[str, Any]:
        action = step.get("action")

        if not action:
            return {
                "status": "denied",
                "requires_confirmation": False,
                "action": None,
            }

        policy_result = self.security_policy.check(action)

        if policy_result == "SAFE":
            return {
                "status": "allowed",
                "requires_confirmation": False,
                "action": action,
            }

        if policy_result == "CONFIRM":
            return {
                "status": "confirmation_required",
                "requires_confirmation": True,
                "action": action,
            }

        return {
            "status": "denied",
            "requires_confirmation": False,
            "action": action,
        }
