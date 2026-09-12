import unittest

from core.openai_backend import OpenAIBackend

class TestOpenAIBackend(unittest.TestCase):
    def test_execute_uses_request_provider(self):
        calls = []
        def runner(request_text):
            calls.append(request_text)
            return 'analysis result'
        backend = OpenAIBackend(agent_runner=runner, request_provider=lambda task_id: 'Проанализируй рынок')
        result = backend.execute({'skill': 'russian-investment-analysis'}, 'task_001')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'task_001')
        self.assertEqual(result['text'], 'analysis result')
        self.assertEqual(calls, ['Проанализируй рынок'])

if __name__ == '__main__':
    unittest.main()
