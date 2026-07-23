import unittest
from tests.ai.support import make

U, C = "local-user", "2026-07"


class TestInteractionJournal(unittest.TestCase):
    def setUp(self):
        self.tmp, self.container, self.ai = make()

    def test_lifecycle_events_appended(self):
        self.ai.conversations.create(U, C, "t")
        self.ai.memory.add_human_authored(U, C, "note", actor="a")
        events = {e.event_type.value for e in self.ai.interaction_journal.list_for_scope(U, C)}
        self.assertIn("conversation_created", events)
        self.assertIn("memory_created", events)

    def test_append_and_read_only_port(self):
        j = self.ai.interaction_journal
        self.assertTrue(hasattr(j, "append"))
        self.assertTrue(hasattr(j, "list_for_scope"))
        for forbidden in ("update", "delete", "clear", "edit", "remove"):
            self.assertFalse(hasattr(j, forbidden), forbidden)

    def test_metadata_only_approved_keys(self):
        self.ai.conversations.create(U, C, "MyTitle")
        created = [e for e in self.ai.interaction_journal.list_for_scope(U, C)
                   if e.event_type.value == "conversation_created"]
        self.assertEqual(created[0].metadata, {"title": "MyTitle"})

    def test_no_message_or_row_content_journaled(self):
        conv = self.ai.conversations.create(U, C, "t")
        self.ai.conversations.append_user_message(conv.conversation_id, U, C, "SUPER-SECRET-ROW-DATA")
        rows = self.container.dal.conn.execute("SELECT metadata_json FROM ai_interactions").fetchall()
        blob = " ".join(r[0] for r in rows)
        self.assertNotIn("SUPER-SECRET-ROW-DATA", blob)   # message content never journaled


if __name__ == "__main__":
    unittest.main()
