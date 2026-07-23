import unittest
from tests.ai.support import make

U = "local-user"


class TestPreferences(unittest.TestCase):
    def setUp(self):
        self.tmp, self.container, self.ai = make()
        self.prefs = self.ai.preferences

    def test_typed_defaults(self):
        self.assertEqual(self.prefs.get(U, "answer_detail"), "standard")
        self.assertTrue(self.prefs.get(U, "conversation_persistence"))
        self.assertIsNone(self.prefs.get(U, "unknown_key"))

    def test_set_get_delete(self):
        self.prefs.set(U, "answer_detail", "detailed")
        self.assertEqual(self.prefs.get(U, "answer_detail"), "detailed")
        self.prefs.delete(U, "answer_detail")
        self.assertEqual(self.prefs.get(U, "answer_detail"), "standard")   # back to default

    def test_conversation_persistence_preference(self):
        self.assertTrue(self.prefs.conversation_persistence_enabled(U))
        self.prefs.set(U, "conversation_persistence", False)
        self.assertFalse(self.prefs.conversation_persistence_enabled(U))

    def test_user_isolation(self):
        self.prefs.set("user-1", "audience", "executive")
        self.assertEqual(self.prefs.get("user-1", "audience"), "executive")
        self.assertEqual(self.prefs.get("user-2", "audience"), "reviewer")   # default, isolated


if __name__ == "__main__":
    unittest.main()
