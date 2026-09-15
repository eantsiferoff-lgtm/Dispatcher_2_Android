import unittest

from core.execution_trace import ExecutionTrace


class TestExecutionTrace(unittest.TestCase):
    def test_records_execution_event(self):
        trace = ExecutionTrace()
        trace.record(request_id='req_001', task_id='task_001', step=1, skill='test-skill', backend='local', status='completed', duration_ms=12.5)
        events = trace.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['request_id'], 'req_001')
        self.assertEqual(events[0]['task_id'], 'task_001')
        self.assertEqual(events[0]['step'], 1)
        self.assertEqual(events[0]['skill'], 'test-skill')
        self.assertEqual(events[0]['backend'], 'local')
        self.assertEqual(events[0]['status'], 'completed')
        self.assertEqual(events[0]['duration_ms'], 12.5)


    def test_records_event_type(self):
        trace = ExecutionTrace()
        trace.record(
            request_id="req_002",
            task_id="task_002",
            step=1,
            skill="test-skill",
            backend="local",
            status="running",
            duration_ms=0.0,
            event_type="started",
        )
        events = trace.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "started")


if __name__ == '__main__':
    unittest.main()
