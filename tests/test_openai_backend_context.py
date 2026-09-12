import unittest

from core.models import Request
from core.openai_backend import OpenAIBackend

class TestOpenAIBackendContext(unittest.TestCase):
    def test_request_provider_returns_original_request_text(self):
        requests = {'task_001': Request(request_id='req_001', text='Проанализируй российский рынок')}
        backend = OpenAIBackend(agent_runner=lambda text: text, request_provider=lambda task_id: requests[task_id].text)
        result = backend.execute({'skill': 'russian-investment-analysis'}, 'task_001')
        self.assertEqual(result['text'], 'Проанализируй российский рынок')

if __name__ == '__main__':
    unittest.main()
