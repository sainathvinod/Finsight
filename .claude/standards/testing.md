# Standard — Testing

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `pyproject.toml` (`[tool.pytest.ini_options]` markers), `.importlinter`, existing `tests/` tree; `NFR-036`, `NFR-037`, `NFR-048`.

## Rule

1. **Test framework and markers.** Tests use `pytest`. The approved markers are: `unit`, `golden`, `determinism`, `fitness`, `audit`, `accessibility`, `security` (`pyproject.toml`). Use the existing marker set; do not invent new marker categories without a spec basis.
2. **Existing suites are the model.** New tests follow the established layout: `tests/unit/`, `tests/golden/`, `tests/determinism/`, `tests/fitness/`, `tests/crashsafety/`, `tests/accessibility/`, plus root suites (`test_audit.py`, `test_provenance.py`, `test_verification_gate.py`, etc.).
3. **Release gates.** Golden-dataset regression, determinism (repeated-run identity), and provider-swap invariance are hard gates (`NFR-036`, `NFR-037`, `NFR-048`; see [financial-determinism.md](financial-determinism.md)). Architecture fitness (`.importlinter` layering + storage confinement) is a gate under `tests/fitness/`.
4. **Traceability.** Each test annotates the requirement/acceptance-criterion it verifies with `# Verifies: <ID>` (see [audit-traceability.md](audit-traceability.md)).
5. **Domain-relevant cases** (when the relevant feature is in scope): original vs. corrected review data; source data unchanged; analysis uses the certified value; complete audit-event creation; verification-gate consistency; findings appear only after a review is selected; deterministic reruns on identical inputs. When the AI layer exists: Fin explains but does not recompute; AI-off completeness.
6. **No invented coverage threshold.** No numeric coverage threshold is defined in the repository today; do not impose one. If a threshold is later added to approved standards, preserve it exactly.

## Escalation

If an acceptance criterion needed to write a test is missing or ambiguous, raise a **Red Card**. Do not invent expected values.
