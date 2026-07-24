import os
import unittest
from tests.ai.support import make, seed_review

_APP_AI = os.path.join("src", "finsight", "application", "ai")
_DOMAIN_AI = os.path.join("src", "finsight", "domain", "ai")
_PROVIDERS = os.path.join("src", "finsight", "infrastructure", "ai", "providers")
# Forbidden modules/names — matched only on actual import statements (not comments/docstrings, which
# legitimately document what is forbidden).
_FORBIDDEN = [
    "sqlite3", "PySide6", "urllib",
    "finsight.domain.rules", "finsight.application.analysis", "finsight.application.verification",
    "finsight.application.transition_engine", "finsight.application.workflow", "FindingsCommandPort",
]


def _scan(base):
    offenders = []
    for dp, _dirs, files in os.walk(base):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            for line in open(os.path.join(dp, fn), encoding="utf-8"):
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    for token in _FORBIDDEN:
                        if token in s:
                            offenders.append((fn, token))
    return offenders


class TestAiArchitecture(unittest.TestCase):
    def test_application_ai_has_no_forbidden_imports(self):
        self.assertEqual(_scan(_APP_AI), [])

    def test_domain_ai_has_no_forbidden_imports(self):
        self.assertEqual(_scan(_DOMAIN_AI), [])

    def test_providers_have_no_forbidden_imports_yet(self):
        # Phase 4C.1: only NullProvider exists. No urllib/HTTP transport, no PySide6, no sqlite3,
        # no deterministic-engine imports. (OllamaProvider introduces urllib in a later sub-phase.)
        self.assertEqual(_scan(_PROVIDERS), [])

    def test_prompt_package_is_pure(self):
        # Phase 4C.2: PromptBuilder is provider-independent and pure — it must not import any
        # provider, infrastructure, UI, DB, or HTTP module.
        base = os.path.join("src", "finsight", "application", "ai", "prompt")
        bad = []
        for dp, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                for line in open(os.path.join(dp, fn), encoding="utf-8"):
                    s = line.strip()
                    if s.startswith("import ") or s.startswith("from "):
                        for tok in ("infrastructure", "provider", "PySide6", "sqlite3", "urllib"):
                            if tok in s:
                                bad.append((fn, tok))
        self.assertEqual(bad, [])

    def test_response_layer_is_pure(self):
        # Phase 4C.4: ResponseValidator and CitationVerifier are provider-independent and side-effect
        # free — no provider, infrastructure, UI, DB, HTTP, PromptBuilder, or orchestration imports.
        base = os.path.join("src", "finsight", "application", "ai")
        bad = []
        for fn in ("validation.py", "citations.py"):
            for line in open(os.path.join(base, fn), encoding="utf-8"):
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    for tok in ("infrastructure", "provider", "PySide6", "sqlite3", "urllib",
                                "repositories", "prompt.builder", "askfin"):
                        if tok in s.lower():
                            bad.append((fn, tok))
        self.assertEqual(bad, [])

    def test_orchestration_layer_is_pure(self):
        # Phase 4C.5: AskFinService/runtime/retry are synchronous application-layer coordinators —
        # no PySide6, asyncio, threading, urllib, sqlite3, infrastructure, provider transport, or
        # deterministic command-path imports.
        base = os.path.join("src", "finsight", "application", "ai")
        bad = []
        for fn in ("ask_fin.py", "ask_fin_contracts.py", "runtime.py", "retry.py"):
            for line in open(os.path.join(base, fn), encoding="utf-8"):
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    for tok in ("pyside6", "asyncio", "threading", "urllib", "sqlite3",
                                "infrastructure", "ollama", "providers.", "repositories"):
                        if tok in s.lower():
                            bad.append((fn, tok))
        self.assertEqual(bad, [])

    def test_ai_operations_do_not_mutate_deterministic_state(self):
        tmp, container, ai = make()
        seed_review(container, tmp, "2026-07")
        before_findings = container.finding_repo.list("2026-07")
        before_state = container.cycle_repo.get("2026-07").state
        before_run = container.run_repo.get_by_cycle("2026-07")
        before_audit = container.audit.timeline("2026-07")

        conv = ai.conversations.create("local-user", "2026-07", "t")
        ai.conversations.append_user_message(conv.conversation_id, "local-user", "2026-07", "q")
        ai.memory.add_human_authored("local-user", "2026-07", "note", actor="a")
        ai.preferences.set("local-user", "answer_detail", "detailed")
        ai.grounding.context("2026-07")

        self.assertEqual(container.finding_repo.list("2026-07"), before_findings)
        self.assertEqual(container.cycle_repo.get("2026-07").state, before_state)
        self.assertEqual(container.run_repo.get_by_cycle("2026-07"), before_run)
        self.assertEqual(container.audit.timeline("2026-07"), before_audit)


if __name__ == "__main__":
    unittest.main()
