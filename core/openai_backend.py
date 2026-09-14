from __future__ import annotations
from typing import Any, Callable

class OpenAIBackend:
    priority = 80

    def __init__(self, agent_runner: Callable[[str], Any] | None = None, request_provider: Callable[[str], str] | None = None):
        self.agent_runner = agent_runner
        self.request_provider = request_provider

    def available(self) -> bool:
        return self.agent_runner is not None

    def can_execute(self, target: Any) -> bool:
        if not isinstance(target, dict) or not self.available():
            return False
        if not target.get('skill'):
            return False
        if target.get('tool_slug') or target.get('workflow'):
            return False
        return target.get('backend') == 'openai' or target.get('execution_mode') == 'ai'

    def execute(self, step: dict[str, Any], task_id: str) -> dict[str, Any]:
        if self.agent_runner is None:
            raise RuntimeError('OpenAI backend is not configured')
        request_text = self.request_provider(task_id) if self.request_provider is not None else step.get('skill', '')
        result = self.agent_runner(request_text)
        return {'status': 'completed', 'task_id': task_id, 'text': str(result)}
