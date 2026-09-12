from __future__ import annotations


class SecurityPolicy:
    SAFE_ACTIONS = {"analyze", "read", "search", "calculate"}
    CONFIRM_ACTIONS = {"send", "delete", "publish", "modify", "purchase"}

    def check(self, action: str) -> str:
        if action in self.SAFE_ACTIONS:
            return "SAFE"
        if action in self.CONFIRM_ACTIONS:
            return "CONFIRM"
        return "DENY"
