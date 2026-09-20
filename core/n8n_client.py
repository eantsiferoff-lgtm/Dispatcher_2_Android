from __future__ import annotations

from typing import Any

import requests


class N8NClient:
    def __init__(self, webhook_url: str, timeout: float = 30.0):
        if not webhook_url:
            raise ValueError("webhook_url must not be empty")
        self.webhook_url = webhook_url
        self.timeout = timeout

    def execute(
        self,
        workflow: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = requests.post(
            self.webhook_url,
            json=payload or {},
            timeout=self.timeout,
        )
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            data = response.text

        return {
            "status": "completed",
            "data": data,
        }
