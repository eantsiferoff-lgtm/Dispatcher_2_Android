import unittest

from core.confirmation_engine import ConfirmationEngine
from core.security_policy import SecurityPolicy


class TestConfirmationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConfirmationEngine(SecurityPolicy())

    def test_safe_action_does_not_require_confirmation(self):
        decision = self.engine.check({"action": "analyze"})

        self.assertEqual(decision["status"], "allowed")
        self.assertFalse(decision["requires_confirmation"])

    def test_consequential_action_requires_confirmation(self):
        decision = self.engine.check({"action": "send"})

        self.assertEqual(decision["status"], "confirmation_required")
        self.assertTrue(decision["requires_confirmation"])

    def test_unknown_action_is_denied(self):
        decision = self.engine.check({"action": "unknown-dangerous-action"})

        self.assertEqual(decision["status"], "denied")
        self.assertFalse(decision["requires_confirmation"])

    def test_missing_action_is_denied(self):
        decision = self.engine.check({})

        self.assertEqual(decision["status"], "denied")
        self.assertFalse(decision["requires_confirmation"])


if __name__ == "__main__":
    unittest.main()
