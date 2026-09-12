import unittest

from core.security_policy import SecurityPolicy


class TestSecurityPolicy(unittest.TestCase):
    def test_safe_action(self):
        policy = SecurityPolicy()
        self.assertEqual(policy.check("analyze"), "SAFE")
        self.assertEqual(policy.check("read"), "SAFE")

    def test_consequential_action_requires_confirmation(self):
        policy = SecurityPolicy()
        for action in ["send", "delete", "publish", "modify", "purchase"]:
            self.assertEqual(policy.check(action), "CONFIRM")

    def test_unknown_action_is_denied(self):
        policy = SecurityPolicy()
        self.assertEqual(policy.check("unknown-dangerous-action"), "DENY")


if __name__ == "__main__":
    unittest.main()
