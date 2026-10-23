import unittest

from app.core.security import hash_password, token_hash, verify_password


class CredentialTests(unittest.TestCase):
    def test_correct_wrong_and_malformed_passwords(self):
        encoded = hash_password("demo-test-only-2026")
        self.assertTrue(verify_password("demo-test-only-2026", encoded))
        self.assertFalse(verify_password("wrong-password", encoded))
        self.assertFalse(verify_password("demo-test-only-2026", "malformed"))
        self.assertNotIn("demo-test-only-2026", encoded)

    def test_each_hash_has_a_different_salt(self):
        self.assertNotEqual(
            hash_password("same-demo-password"), hash_password("same-demo-password")
        )

    def test_token_digest_is_deterministic_without_storing_plain_token(self):
        self.assertEqual(token_hash("demo-token"), token_hash("demo-token"))
        self.assertNotEqual(token_hash("demo-token"), "demo-token")
        self.assertEqual(len(token_hash("demo-token")), 64)
