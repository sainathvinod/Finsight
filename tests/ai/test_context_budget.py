import unittest
from finsight.application.ai.prompt.budget import ContextBudget

_FIELDS = ["max_findings", "max_conversation_messages", "max_memory_entries",
           "max_provenance_items", "max_audit_events"]


class TestContextBudgetValidation(unittest.TestCase):
    def test_none_zero_and_positive_are_valid(self):
        for f in _FIELDS:
            ContextBudget(**{f: None})   # unlimited
            ContextBudget(**{f: 0})      # retain zero
            ContextBudget(**{f: 7})      # positive

    def test_negative_rejected_for_every_field(self):
        for f in _FIELDS:
            with self.assertRaises(ValueError, msg=f):
                ContextBudget(**{f: -1})

    def test_boolean_rejected_for_every_field(self):
        # bool subclasses int in Python, but is not a valid limit
        for f in _FIELDS:
            with self.assertRaises(ValueError, msg="%s=True" % f):
                ContextBudget(**{f: True})
            with self.assertRaises(ValueError, msg="%s=False" % f):
                ContextBudget(**{f: False})

    def test_non_integer_rejected_for_every_field(self):
        for f in _FIELDS:
            for bad in (1.5, "3", [1], 2.0):
                with self.assertRaises(ValueError, msg="%s=%r" % (f, bad)):
                    ContextBudget(**{f: bad})


if __name__ == "__main__":
    unittest.main()
