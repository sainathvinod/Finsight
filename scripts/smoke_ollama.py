"""Manual, developer-only smoke test for the local Ollama integration (Phase 4C.6A).

THIS IS NOT PART OF THE SHIPPED APP AND IS NOT A TEST. It performs real local network calls and is run
by hand. Importing this module runs nothing (all work is inside functions guarded by __main__).

Run instructions (local developer):
  1. Start Ollama:                 `ollama serve`
  2. Pull the configured model:    `ollama pull llama3.2:3b`
  3. Set the environment:
         export FINSIGHT_AI_PROVIDER=ollama
         export FINSIGHT_AI_DEMO_AUTHORIZED=true      # LOCAL DEMO ONLY — not production consent
     (optional, for the full-pipeline mode against an existing review:)
         export FINSIGHT_DB=/path/to/finsight.db
         export FINSIGHT_SMOKE_CYCLE=<existing cycle_id>
  4. Run:                          `python -m scripts.smoke_ollama`
  5. Note: FINSIGHT_AI_DEMO_AUTHORIZED is a fail-closed development gate only. It is NOT production
     consent (FR-096), stores nothing, and grants no enterprise/role authorization. Production stays
     fail-closed unless an authorization policy is explicitly wired.

Two clearly-distinguished modes:
  * Provider-transport smoke  — synthetic in-memory grounding through Masking → PromptBuilder →
    OllamaProvider → ResponseValidator → CitationVerifier. No database, no deterministic state touched.
  * Full AskFin-pipeline smoke — only when FINSIGHT_DB + FINSIGHT_SMOKE_CYCLE are set; runs the real
    AskFinService against an EXISTING review (read-only).

It prints only safe status and the developer-facing validated answer. It never prints raw prompts or
raw provider envelopes, never persists raw provider output, and never modifies deterministic state.
"""
from __future__ import annotations
import os
import sys


def _die(message: str) -> int:
    print("SMOKE ABORT:", message)
    return 2


def run_provider_smoke(settings) -> int:
    """Synthetic, DB-free path through the real transport + validation components."""
    from finsight.application.ai.citations import CitationVerifier
    from finsight.application.ai.masking import MaskingService
    from finsight.application.ai.prompt.budget import ContextBudget
    from finsight.application.ai.prompt.builder import PromptBuilder
    from finsight.application.ai.validation import ResponseValidator
    from finsight.domain.ai.contracts import (
        AiGroundingContext, GroundedFinding, GroundedReview,
    )
    from finsight.infrastructure.ai.providers.ollama import OllamaProvider

    provider = OllamaProvider(settings.provider_config,
                              status_timeout=settings.status_timeout_seconds, enabled=True)
    status = provider.status()
    print("provider status: generation_available=%s reason=%s model=%s"
          % (status.generation_available, status.reason, settings.provider_config.model))
    if not status.generation_available:
        return _die("Ollama not generation-available (see reason above)")

    grounding = AiGroundingContext(
        review=GroundedReview("demo", "July", "2026", "Exported", 1),
        findings=[GroundedFinding("F1", "6100", "R-BUD-02", "High", "variance", "2026-07",
                                  {"variance_pct": "12.5", "amount": "1000"}, ["GED:6100"], "New")])
    masked = MaskingService().mask(grounding=grounding, question="Explain finding F1 briefly.")
    built = PromptBuilder(ContextBudget()).build(
        grounding=masked.grounding, question=masked.question,
        conversation=masked.conversation, memory=masked.memory)
    try:
        raw = provider.generate(built.request, settings.provider_config)
    except Exception as exc:                                 # provider transport error — safe code only
        return _die("provider call failed: %s (%s)" % (type(exc).__name__, getattr(exc, "code", "")))

    try:
        validated = ResponseValidator(settings.validation_limits).validate(
            raw.text, schema_version=built.request.schema_version)
        citations = CitationVerifier().verify(validated, built.citation_index)
    except Exception as exc:
        return _die("response rejected by validation/citations: %s (%s)"
                    % (type(exc).__name__, getattr(exc, "code", "")))

    print("provider transport smoke OK: provider=%s model=%s unable_to_answer=%s citations=%s"
          % (raw.provider, raw.model, validated.unable_to_answer, [c.key for c in citations]))
    print("validated answer:", validated.answer_text)       # developer-facing validated answer only
    return 0


def run_pipeline_smoke(settings, db_path: str, cycle_id: str) -> int:
    """Full AskFin pipeline against an EXISTING review (read-only) using demo authorization."""
    from finsight.app import build_app, build_ai_services, build_demo_ai_explanation_service
    from finsight.application.ai.ask_fin_contracts import AskFinRequest
    from finsight.infrastructure.clock import SystemClock

    container = build_app(db_path, SystemClock())
    ai = build_ai_services(container)
    explanation = build_demo_ai_explanation_service(container, ai, settings=settings)
    print("pipeline provider status: generation_available=%s reason=%s"
          % (explanation.provider_status.generation_available, explanation.provider_status.reason))
    result = explanation.ask_fin.explain(
        AskFinRequest(user_id="local-user", cycle_id=cycle_id, question="Explain this review briefly."))
    print("AskFin result: status=%s grounding_confidence=%s citations=%d last_stage=%s error=%s"
          % (result.status.value, result.metadata.grounding_confidence, result.metadata.citation_count,
             result.metadata.last_stage, result.metadata.error_code))
    if result.answer is not None:
        print("validated answer:", result.answer.answer_text)  # developer-facing validated answer only
    return 0


def main(env=None) -> int:
    env = os.environ if env is None else env
    from finsight.infrastructure.ai.config import AiConfigError, load_ai_runtime_settings
    try:
        settings = load_ai_runtime_settings(env=env)
    except AiConfigError as exc:
        return _die("invalid AI configuration: %s" % exc)

    if settings.provider != "ollama":
        return _die("set FINSIGHT_AI_PROVIDER=ollama")
    if not settings.demo_authorized:
        return _die("set FINSIGHT_AI_DEMO_AUTHORIZED=true (local demo only; not production consent)")

    rc = run_provider_smoke(settings)
    if rc != 0:
        return rc

    db_path, cycle_id = env.get("FINSIGHT_DB"), env.get("FINSIGHT_SMOKE_CYCLE")
    if db_path and cycle_id:
        print("--- full AskFin pipeline smoke (existing review, read-only) ---")
        return run_pipeline_smoke(settings, db_path, cycle_id)
    print("(skipping full-pipeline smoke: set FINSIGHT_DB and FINSIGHT_SMOKE_CYCLE to enable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
