import unittest
from tests.ai.support import make
from finsight.domain.ai.contracts import MemoryType
from finsight.application.ai.errors import MemoryProvenanceError, AiScopeError

U, C = "local-user", "2026-07"


class TestReviewMemory(unittest.TestCase):
    def setUp(self):
        self.tmp, self.container, self.ai = make()
        self.mem = self.ai.memory

    def test_human_authored_round_trip(self):
        e = self.mem.add_human_authored(U, C, "Vendor X is under review", actor="analyst")
        self.assertEqual(e.memory_type, MemoryType.HUMAN_AUTHORED)
        entries = self.mem.list(U, C)
        self.assertEqual([x.content for x in entries], ["Vendor X is under review"])
        self.assertEqual(entries[0].actor, "analyst")

    def test_system_derived_requires_source(self):
        with self.assertRaises(MemoryProvenanceError):
            self.mem.add_system_derived(U, C, "derived note", source_type="", source_id="", actor="system")
        e = self.mem.add_system_derived(U, C, "finding 6100 acknowledged",
                                        source_type="finding", source_id="F-abc-6100", actor="system")
        self.assertEqual(e.memory_type, MemoryType.SYSTEM_DERIVED)
        self.assertEqual(e.source_type, "finding")
        self.assertEqual(e.source_id, "F-abc-6100")

    def test_model_authored_is_impossible(self):
        # Only two provenance types exist; there is no API accepting model output.
        self.assertEqual({m.value for m in MemoryType}, {"human_authored", "system_derived"})
        for forbidden in ("add_model_authored", "add_from_model", "remember_model_output"):
            self.assertFalse(hasattr(self.mem, forbidden), forbidden)

    def test_review_isolation(self):
        self.mem.add_human_authored(U, "2026-07", "note A", actor="a")
        self.mem.add_human_authored(U, "2026-08", "note B", actor="a")
        self.assertEqual([e.content for e in self.mem.list(U, "2026-07")], ["note A"])
        self.assertEqual([e.content for e in self.mem.list(U, "2026-08")], ["note B"])

    def test_user_isolation(self):
        self.mem.add_human_authored("user-1", C, "u1 note", actor="a")
        self.mem.add_human_authored("user-2", C, "u2 note", actor="a")
        self.assertEqual([e.content for e in self.mem.list("user-1", C)], ["u1 note"])
        self.assertEqual([e.content for e in self.mem.list("user-2", C)], ["u2 note"])

    def test_delete_one_entry(self):
        e1 = self.mem.add_human_authored(U, C, "one", actor="a")
        self.mem.add_human_authored(U, C, "two", actor="a")
        self.mem.delete_entry(U, C, e1.memory_id)
        self.assertEqual([e.content for e in self.mem.list(U, C)], ["two"])

    def test_delete_entry_scope_guard(self):
        e = self.mem.add_human_authored(U, C, "one", actor="a")
        with self.assertRaises(AiScopeError):
            self.mem.delete_entry("other-user", C, e.memory_id)

    def test_forget_review_scoped(self):
        self.mem.add_human_authored(U, "2026-07", "a", actor="x")
        self.mem.add_human_authored(U, "2026-07", "b", actor="x")
        self.mem.add_human_authored(U, "2026-08", "keep", actor="x")
        removed = self.mem.forget_review(U, "2026-07")
        self.assertEqual(removed, 2)
        self.assertEqual(self.mem.list(U, "2026-07"), [])
        self.assertEqual([e.content for e in self.mem.list(U, "2026-08")], ["keep"])   # other review intact


if __name__ == "__main__":
    unittest.main()
