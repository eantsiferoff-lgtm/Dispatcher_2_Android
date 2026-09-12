import unittest

from core.execution_router import ExecutionRouter
from core.local_backend import LocalBackend
from core.openai_backend import OpenAIBackend
from core.skill_executor import SkillExecutor


class TestBackendFallback(unittest.TestCase):
    def test_openai_is_fallback_when_local_cannot_execute(self):
        skills = SkillExecutor()
        skills.register('local-skill', lambda step, task_id: {'text': 'local'})
        local = LocalBackend(skills)
        openai = OpenAIBackend(agent_runner=lambda text: 'ai')
        router = ExecutionRouter()
        router.register('local', local)
        router.register('openai', openai)
        self.assertEqual(router.route({'skill': 'local-skill'}), 'local')
        self.assertEqual(router.route({'skill': 'ai-skill'}), 'openai')


if __name__ == '__main__':
    unittest.main()
