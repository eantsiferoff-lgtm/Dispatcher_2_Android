import unittest

from core.openai_backend import OpenAIBackend

class TestOpenAIBackendRealAdapter(unittest.TestCase):
    def test_runner_receives_request_text(self):
        calls = []
        def runner(request_text):
            calls.append(request_text)
            return 'AI_RESULT'
        backend = OpenAIBackend(agent_runner=runner, request_provider=lambda task_id: 'Проанализируй российский рынок')
        result = backend.execute({'skill': 'russian-investment-analysis'}, 'task_123')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'task_123')
        self.assertEqual(result['text'], 'AI_RESULT')
        self.assertEqual(calls, ['Проанализируй российский рынок'])

if __name__ == '__main__':
    unittest.main()
