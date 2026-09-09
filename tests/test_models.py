import unittest
from core.models import Request, Plan, Task, Result

class TestModels(unittest.TestCase):
    def test_request(self):
        r = Request('REQ-000001', 'Тестовый запрос')
        self.assertEqual(r.request_id, 'REQ-000001')
        self.assertEqual(r.text, 'Тестовый запрос')

    def test_plan(self):
        p = Plan('REQ-000001', ['russian-investment-analysis'])
        self.assertEqual(p.skills, ['russian-investment-analysis'])

    def test_task(self):
        p = Plan('REQ-000001')
        t = Task('TASK-000001', 'REQ-000001', plan=p)
        self.assertEqual(t.status, 'pending')
        self.assertIs(t.plan, p)

    def test_result(self):
        r = Result('TASK-000001', 'completed', 'Готово')
        self.assertEqual(r.status, 'completed')
        self.assertEqual(r.text, 'Готово')

if __name__ == '__main__':
    unittest.main()
