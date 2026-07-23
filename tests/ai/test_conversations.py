import unittest
from tests.ai.support import make
from finsight.application.ai.errors import AiScopeError, ConversationNotFoundError

U, C = "local-user", "2026-07"


class TestConversations(unittest.TestCase):
    def setUp(self):
        self.tmp, self.container, self.ai = make()
        self.conv = self.ai.conversations

    def test_create_list_load_rename(self):
        c = self.conv.create(U, C, "May budget questions")
        listed = self.conv.list(U, C)
        self.assertEqual([x.conversation_id for x in listed], [c.conversation_id])
        conv, msgs = self.conv.load(c.conversation_id, U, C)
        self.assertEqual(conv.title, "May budget questions")
        self.assertEqual(msgs, [])
        self.conv.rename(c.conversation_id, U, C, "Renamed")
        conv2, _ = self.conv.load(c.conversation_id, U, C)
        self.assertEqual(conv2.title, "Renamed")

    def test_append_and_order(self):
        c = self.conv.create(U, C, "t")
        self.conv.append_user_message(c.conversation_id, U, C, "first")
        self.conv.append_assistant_message(c.conversation_id, U, C, "second")
        self.conv.append_user_message(c.conversation_id, U, C, "third")
        _, msgs = self.conv.load(c.conversation_id, U, C)
        self.assertEqual([m.content for m in msgs], ["first", "second", "third"])
        self.assertEqual([m.seq for m in msgs], [1, 2, 3])   # deterministic ordering

    def test_clear_preserves_conversation(self):
        c = self.conv.create(U, C, "t")
        self.conv.append_user_message(c.conversation_id, U, C, "hi")
        self.conv.clear_messages(c.conversation_id, U, C)
        conv, msgs = self.conv.load(c.conversation_id, U, C)   # conversation still loads
        self.assertEqual(msgs, [])

    def test_delete_removes_conversation_and_messages(self):
        c = self.conv.create(U, C, "t")
        self.conv.append_user_message(c.conversation_id, U, C, "hi")
        self.conv.delete(c.conversation_id, U, C)
        self.assertEqual(self.conv.list(U, C), [])
        with self.assertRaises(ConversationNotFoundError):
            self.conv.load(c.conversation_id, U, C)
        # cascade: messages gone
        rows = self.container.dal.conn.execute(
            "SELECT COUNT(*) FROM ai_messages WHERE conversation_id=?", (c.conversation_id,)).fetchone()[0]
        self.assertEqual(rows, 0)

    def test_scope_mismatch_rejected(self):
        c = self.conv.create(U, C, "t")
        with self.assertRaises(AiScopeError):
            self.conv.load(c.conversation_id, "other-user", C)
        with self.assertRaises(AiScopeError):
            self.conv.load(c.conversation_id, U, "2099-01")

    def test_retention_disabled_does_not_persist_content(self):
        self.ai.preferences.set(U, "conversation_persistence", False)
        c = self.conv.create(U, C, "t")
        msg = self.conv.append_user_message(c.conversation_id, U, C, "should-not-persist")
        self.assertEqual(msg.seq, -1)          # transient
        _, msgs = self.conv.load(c.conversation_id, U, C)
        self.assertEqual(msgs, [])             # nothing stored


if __name__ == "__main__":
    unittest.main()
