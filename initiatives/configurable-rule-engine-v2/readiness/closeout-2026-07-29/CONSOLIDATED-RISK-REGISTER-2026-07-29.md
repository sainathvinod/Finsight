# FinSight V2 Consolidated Risk Register

**Date:** 2026-07-29
**Review scope:** deterministic financial correctness, supported sources, UX and
accessibility, reports/exports, Ask Fin privacy/security/runtime, Windows packaging,
licensing, deployment, recovery, and operations
**Review type:** Independent, read-only closeout assessment
**Decision:** **FAIL — not ready to begin release packaging**

## 1. Executive assessment

This register contains **20 consolidated risks**. FinSight has a strong
application-level Ask Fin boundary. The reviewed implementation
restricts the provider to verified loopback HTTP endpoints, rejects redirects and proxy
inheritance, re-verifies the exact local model before every prompt, enforces
review/authorization scope, verifies structured claims and citations, rejects
decision-making language, and fails closed when the immutable AI audit cannot be
persisted. The focused security/runtime/packaging-support test set completed with
**204 passed and 2 subtests passed**.

Those controls do not make the product release-ready. The current repository-wide
baseline is red, material financial and architecture defects remain open, no native
Windows executable or MSI build exists, no clean-machine Windows lifecycle has been
qualified, and the Ollama/model deployment and licensing contract is unresolved.
Several additional Ask Fin controls are adequate for development but not yet sufficient
for a governed pilot: the default model trust flow is session-scoped trust on first use,
the Ollama daemon's outbound/cloud behavior is not deployment-enforced, and provider
response size and concurrency are not authoritatively bounded.

### Release decision

- **Packaging may not start** until RR-01 through RR-07, RR-15, RR-17, and RR-20 are
  closed or an approved requirements change explicitly removes the affected release
  obligation.
- **A pilot may not start** until every packaging blocker is closed and RR-08 through
  RR-14 and RR-19 are closed.
- RR-16 is an accepted local-computer trust boundary only if it is documented,
  deployment controls are applied, and the residual risk is formally accepted.
- RR-18 is an acceptable first-release layout limitation only for a pilot whose files
  are prequalified against `SLV-001` and whose source-retention duty is explicit.

## 2. Classification and rating method

| Classification | Meaning |
|---|---|
| Must fix before packaging | Blocks creation of the governed Windows release candidate or makes its contents/support contract undefined. |
| Must fix before pilot | May be completed after the packaging build path exists, but blocks use with pilot financial data or pilot users. |
| Should fix | Does not block the first controlled pilot if explicitly accepted, but materially improves supportability or reduces avoidable risk. |
| Optional | Useful enhancement with no current release or pilot obligation. |
| Deferred | Governed future scope that must not be represented as delivered. |

| Rating | Likelihood or impact interpretation |
|---|---|
| Low | Unlikely or limited, recoverable effect. |
| Medium | Credible occurrence or meaningful operational/user effect. |
| High | Likely or severe effect on correctness, confidentiality, integrity, availability, or release support. |
| Critical | Could invalidate the release, expose sensitive financial data, or undermine the authoritative validation/audit contract. |

## 3. Risk register

### RR-01 — Release baseline is red and not reproducibly frozen

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | The current full suite records **4 failed, 1,212 passed, 2 subtests passed**. Failures include 200% appearance clipping, an inaccessible Settings Back button, order-dependent Ask Fin drawer sizing, and a prohibited delivery-to-infrastructure dependency. The closeout inventory also records material financial defects and a large uncommitted worktree. |
| Components/files | `CONSOLIDATED-TEST-INVENTORY-2026-07-29.md`; `UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md`; `src/finsight/delivery/desktop/ask_fin_preferences.py`; current Git worktree |
| Required action | Resolve all material correctness, architecture, accessibility, and order-dependence defects; reconcile the governed baseline; commit a single release candidate; rerun the complete suite and required static/dependency checks from that exact commit. |
| Rationale | Packaging an unstable or unidentifiable source state makes every downstream binary, signature, SBOM, and validation result non-reproducible. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **High**; severity **Critical**. |
| Packaging blocker | **Yes — unconditional.** |
| Pilot blocker | **Yes.** |
| Verification | Timestamped clean full-suite report; architecture/import-linter pass; financial oracle pass; clean `git status`; commit SHA recorded in release manifest and artifacts. |
| Suggested owner | Application Engineering Lead with Financial Validation Lead and QA Lead |

### RR-02 — Native Windows executable and MSI build chain do not exist

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | FR-175 and NFR-094 are Not Started. `tests/ui/test_packaging.py` validates source/module launch, not a frozen application. `docs/DISTRIBUTION.md` documents wheel/zipapp operation and explicitly states that native installers were not built. No PyInstaller specification, WiX source, signed EXE, or MSI was found. |
| Components/files | `tests/ui/test_packaging.py`; `docs/DISTRIBUTION.md`; `ADR-V2-004-windows-packaging-and-support.md`; `UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md` |
| Required action | Implement a pinned, reproducible Windows build that freezes the application and resources, produces a per-machine or otherwise approved MSI with WiX, records versions/hashes, and runs only from the staged release commit. |
| Rationale | A source launch proves neither packaged imports/resources nor installer behavior. The required Windows deliverable is absent. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **High**; severity **Critical**. |
| Packaging blocker | **Yes — unconditional.** |
| Pilot blocker | **Yes.** |
| Verification | Reproducible EXE/MSI hashes from controlled builders; frozen-app smoke tests; MSI validation; installed launch without Python, terminal, or source tree. |
| Suggested owner | Release/Build Engineering |

### RR-03 — Windows-native identity, encryption, ACL, and runtime controls are unqualified

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | FR-176, FR-189, NFR-028, and NFR-029 are incomplete. The adapters and tests cover identity, secure store, authorization, and runtime paths, but no target-Windows evidence verifies SID identity, DPAPI behavior, SQLCipher loading, directory/file ACLs, standard-user execution, PySide6 resources, or equivalent deterministic results. POSIX permission checks do not establish Windows ACL behavior. |
| Components/files | `src/finsight/infrastructure/identity.py`; `secure_store.py`; `runtime_paths.py`; `authorization_manifest.py`; `authorization_source.py`; persistence/ADR security documents; related infrastructure/security tests |
| Required action | Qualify the frozen application on the supported Windows matrix using native SIDs, DPAPI, SQLCipher, explicit ACL assertions, standard-user accounts, multiple Windows actors, and byte-equivalent financial result fixtures. |
| Rationale | Security and identity behavior can change materially when code is frozen and run under Windows APIs and filesystem semantics. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Packaging blocker | **Yes — the package cannot be declared secure or supported.** |
| Pilot blocker | **Yes.** |
| Verification | Automated and manual Windows security matrix; ACL/SID/DPAPI evidence; encrypted-at-rest inspection; cross-platform oracle comparison; no plaintext secrets or review content in install/log/temp paths. |
| Suggested owner | Security Engineering with Windows Platform Engineering |

### RR-04 — Installer lifecycle, recovery, and disposal are not implemented or qualified

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | FR-177 and NFR-101 are Not Started. Repair, in-place upgrade, rollback, uninstall, replacement-machine restore, registry continuity, and complete disposal remain architecture/planning obligations without production lifecycle evidence. |
| Components/files | `ADR-V2-003-encrypted-authoritative-persistence-and-recovery.md`; `PERSISTENCE-MODEL.md`; `ADR-V2-004-windows-packaging-and-support.md`; review-disposal implementation/tests; traceability matrix |
| Required action | Either implement the approved lifecycle or change scope through governance before release. Define data-preserving upgrade/repair, explicit uninstall data policy, backup/restore including registry and audit continuity, and cryptographically/operationally verifiable disposal. |
| Rationale | A financial review product cannot safely ship without a supported recovery and data-lifecycle contract. Installer errors or upgrades could strand, expose, or silently replace authoritative history. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Packaging blocker | **Yes — unconditional while these remain release requirements.** |
| Pilot blocker | **Yes.** |
| Verification | Clean-VM install/repair/upgrade/rollback/uninstall matrix; power-loss and corrupted-upgrade drills; backup to replacement machine; audit/registry continuity; retained-versus-removed data assertions. |
| Suggested owner | Persistence Lead with Release Engineering and Security |

### RR-05 — Signing, provenance, SBOM, malware scanning, and release custody are absent

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | FR-178 and NFR-095 are Not Started. No signed candidate, certificate-custody procedure, timestamping, release SBOM, provenance attestation, checksums, malware scan, or tamper verification was found. |
| Components/files | `ADR-V2-004-windows-packaging-and-support.md`; `DEPENDENCIES.md`; dependency qualification report; traceability matrix |
| Required action | Establish a controlled Windows release runner; protect signing credentials; Authenticode-sign and timestamp EXE/MSI; generate CycloneDX or SPDX SBOM and dependency/license notices; publish hashes/provenance; scan final artifacts; test tamper and signature failure. |
| Rationale | Financial desktop software must give users and administrators a verifiable publisher and exact software bill of materials. Unsigned or untraceable binaries are not enterprise-deployable. |
| Impact / likelihood / severity | Impact **High**; likelihood **High**; severity **High**. |
| Packaging blocker | **Yes — no release candidate is governable without it.** |
| Pilot blocker | **Yes.** |
| Verification | Valid signature and trusted timestamp on clean Windows; SBOM matches frozen contents; hashes match release manifest; malware scan reports; modified binary rejected/detected. |
| Suggested owner | Release Engineering with Security/PKI |

### RR-06 — Third-party license and redistribution obligations are unresolved

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | Dependency inventories exist, but no legal approval or packaged notice bundle proves obligations for the frozen Python/Qt application, SQLCipher, PyInstaller, WiX binary tooling, Ollama, or the default Meta Llama 3.2 model. The model uses a custom community license, not the Ollama engine's MIT license, and includes attribution/redistribution conditions. |
| Components/files | `DEPENDENCIES.md`; `requirements*.txt`; `pyproject.toml`; dependency qualification report; planned PyInstaller/WiX/Ollama/model artifacts |
| Required action | Inventory exact packaged binaries and transitive licenses; obtain legal approval; select commercial or LGPL-compliant Qt distribution posture; include SQLCipher and other required notices; pin WiX version/terms; decide whether Ollama/model are redistributed; if Llama is bundled, satisfy its agreement, attribution, notice, and acceptable-use obligations. |
| Rationale | Packaging changes legal scope from development use to distribution. Engine and model licenses are separate and cannot be inferred from each other. |
| Impact / likelihood / severity | Impact **High**; likelihood **High**; severity **High**. |
| Packaging blocker | **Yes — contents cannot be finalized before distribution rights/obligations are known.** |
| Pilot blocker | **Yes.** |
| Verification | Counsel-approved license matrix; user-accessible Third-Party Notices; SBOM-to-notice reconciliation; automated notice-presence test; redistribution decision recorded. |
| Suggested owner | Product Legal/Open Source Program Office with Release Engineering |

### RR-07 — Ollama/model packaging and first-run topology are undefined

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | FinSight detects a local provider but does not install, start, repair, or download Ollama/model assets. Official Ollama Windows behavior is primarily per-user, with per-user app/model locations and auto-update, while FinSight's governed store supports shared machine use and multiple Windows actors. The traceability matrix nevertheless calls for automatic runtime/model provisioning. |
| Components/files | `src/finsight/app.py`; `private_config.py`; `providers/ollama.py`; `ask_fin_preferences.py`; `ADR-V2-004-windows-packaging-and-support.md`; Windows/Ask Fin architecture documents |
| Required action | Choose and govern one automatic topology: (A) a coordinated enterprise deployment that installs/configures the exact Ollama/model dependency before FinSight without end-user action, or (B) a FinSight-owned packaged/provisioned runtime and model. Both require service identity, cache design, offline payload strategy, license approval, repair, update, uninstall ownership, and a no-terminal/no-manual-start first run. A merely documented manual prerequisite is insufficient. |
| Rationale | The MSI contents, size, privileges, service/cache ownership, offline behavior, support model, and license obligations all depend on this decision. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **High**; severity **Critical**. |
| Packaging blocker | **Yes — package scope and prerequisites are undefined.** |
| Pilot blocker | **Yes.** |
| Verification | Approved topology ADR/delta; standard-user first-run test; provider absent/present/corrupt scenarios; offline installation or documented managed prerequisite; multi-actor test; no silent cloud fallback. |
| Suggested owner | Solution Architect with Windows Platform, Security, and Legal |

### RR-08 — Default model identity uses session-scoped trust on first use

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | `OllamaProvider` accepts a managed `FINSIGHT_OLLAMA_MODEL_DIGEST`, but when absent it pins the first verified digest only for that provider instance. `AskFinPreferenceStore` intentionally removes the former saved digest. A restart therefore establishes a new first-observed pin. |
| Components/files | `src/finsight/infrastructure/ai/providers/ollama.py`; `private_config.py`; `src/finsight/delivery/desktop/ask_fin_preferences.py`; Ask Fin simplification/architecture delta |
| Required action | For pilot and managed deployments, provision an immutable approved model digest/profile through an administrator-controlled configuration source, protect it from ordinary user edits, include it in release/deployment provenance, and fail closed on mismatch. If TOFU remains for personal development, label and isolate that mode. |
| Rationale | A wrong or malicious loopback service present at first contact can become trusted for the session, and restart resets that trust. Pre-prompt re-verification protects continuity, not first-observation authenticity. |
| Impact / likelihood / severity | Impact **High**; likelihood **Medium**; severity **High**. |
| Packaging blocker | Conditional: **Yes if Ask Fin is enabled in the packaged pilot image; otherwise no if explicitly disabled.** |
| Pilot blocker | **Yes.** |
| Verification | Managed digest injection test; ordinary-user modification denied; wrong/missing/changed digest fails closed; restart preserves approved identity; audit records exact digest/profile. |
| Suggested owner | Security Engineering with AI Runtime Owner |

### RR-09 — Local daemon cloud egress, rebinding, and auto-update are not deployment-enforced

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | FinSight itself validates loopback endpoints, disables urllib proxy inheritance, rejects redirects, and blocks cloud/remote model aliases. Ollama can separately enable cloud features, bind to other interfaces through `OLLAMA_HOST`, use proxies/tunnels, and auto-update. The application does not prove or enforce the daemon's process-level egress state. |
| Components/files | `src/finsight/domain/ai/local_endpoint.py`; `providers/ollama.py`; Stage 2 threat model; Windows deployment policy |
| Required action | Configure Ollama with cloud disabled (`OLLAMA_NO_CLOUD=1` or approved equivalent), bind only to loopback, block outbound egress and unauthorized inbound access with Windows Firewall/WDAC/AppLocker or enterprise policy, control updates, and expose a diagnostic that reports the enforced posture without leaking financial content. |
| Rationale | “FinSight only calls loopback” is not equivalent to “the local model process cannot send data elsewhere.” The provider process is part of the processing boundary. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Packaging blocker | Conditional: **Yes when packaging includes or enables Ask Fin for pilot.** |
| Pilot blocker | **Yes.** |
| Verification | Network-capture and firewall tests during status/chat/model operations; cloud feature request fails; service listens only on loopback; policy survives restart/update; logs show cloud disabled. |
| Suggested owner | Security Engineering with Endpoint Management |

### RR-10 — Provider response size and concurrency are not authoritatively bounded

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | Request/status timeouts exist and the UI disables Send during a request. However, `_request()` uses an unbounded response-body `read()`, `FINSIGHT_AI_MAX_OUTPUT_TOKENS` may be unset so `num_predict` is omitted, and no service-level semaphore or queue enforces a single bounded inference across non-UI callers. |
| Components/files | `src/finsight/infrastructure/ai/providers/ollama.py`; `private_config.py`; `private_ask_fin.py`; private Ask Fin dialog/controller |
| Required action | Set a governed output-token default and maximum; cap response bytes while streaming/reading; reject oversized/invalid responses; enforce service-level concurrency and cancellation; define queue/full behavior; bound prompt/corpus serialization independently of UI state. |
| Rationale | A local provider can still exhaust memory/CPU or hang multiple requests. UI-only mutual exclusion is not a security or availability boundary. |
| Impact / likelihood / severity | Impact **High**; likelihood **Medium**; severity **High**. |
| Packaging blocker | No, if Ask Fin is packaged disabled by default; otherwise release owner must treat it as a packaging blocker. |
| Pilot blocker | **Yes.** |
| Verification | Oversized-body, infinite/slow stream, excessive-token, parallel-controller, cancel, and recovery tests; process memory/CPU thresholds; no audit/result corruption. |
| Suggested owner | AI Runtime Engineering |

### RR-11 — Supported hardware and model performance are not qualified

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | The default model is `llama3.2:3b`. Official listings show an approximately 2 GB model artifact, while Ollama's Windows runtime and model storage require additional disk and memory. No measured cold-start, first-token, completion, CPU/GPU, RAM, disk, or concurrent-application behavior exists for the approved Windows 11 8 GB and 16 GB classes. |
| Components/files | `src/finsight/domain/ai/contracts.py`; `private_config.py`; packaging ADR; performance NFRs/traceability matrix |
| Required action | Define supported hardware, disk headroom, and latency/error budgets; benchmark packaged FinSight plus approved Ollama/model on clean 8 GB and 16 GB Windows 11 systems with CPU-only and supported GPU paths; define degradation/disable behavior. |
| Rationale | An optional feature can still make the desktop application unusable if it consumes unsupported resources or has unbounded latency. |
| Impact / likelihood / severity | Impact **High**; likelihood **High** on minimum hardware; severity **High**. |
| Packaging blocker | No, provided the package accurately declares the unqualified feature unavailable. |
| Pilot blocker | **Yes if Ask Fin is in pilot scope.** |
| Verification | Repeatable benchmark report; peak RAM/disk/CPU/GPU; cold/warm latency; cancellation and low-resource behavior; documented support matrix and installer preflight. |
| Suggested owner | Performance Engineering with Product Support |

### RR-12 — Ollama/model update, repair, rollback, and uninstall ownership is undefined

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | Official Ollama Windows installation can auto-update, and uninstalling the application/runtime does not necessarily remove downloaded models. FinSight verifies the model but has no governed update ring, compatibility manifest, repair mechanism, rollback procedure, or cache-retention policy. |
| Components/files | Windows packaging ADR; Ask Fin runtime/configuration code; deployment and support documentation |
| Required action | Pin supported Ollama/model versions and digest; disable uncontrolled updates; define staged update approval, compatibility testing, rollback, repair, cache retention/removal, and ownership for bundled versus enterprise-managed topology. |
| Rationale | An automatic runtime/model change can make Ask Fin unavailable, change performance, or violate the approved model identity without changing FinSight itself. |
| Impact / likelihood / severity | Impact **High**; likelihood **High** if default auto-update remains; severity **High**. |
| Packaging blocker | Conditional on a bundled/enabled Ask Fin topology. |
| Pilot blocker | **Yes.** |
| Verification | Approved-version manifest; forced old/new/corrupt/mismatch scenarios; rollback test; uninstall data-policy test; release-ring audit. |
| Suggested owner | Release Engineering with AI Runtime Owner |

### RR-13 — AI audit retention, backup/restore, and disposal are incomplete

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | Ask Fin stores raw questions and answers in the encrypted authoritative audit and withholds successful answers when audit persistence fails. That is a strong integrity control, but governed retention, user-content deletion/disposal, portable backup/restore, and replacement-machine continuity are not implemented or qualified; NFR-101 remains Not Started. |
| Components/files | `src/finsight/infrastructure/ai/private_audit.py`; `private_ask_fin.py`; SQLCipher persistence; ADR-009; ADR-010; persistence model; review disposal services |
| Required action | Define minimum/maximum retention and legal hold; incorporate AI records into review/all-data disposal; implement encrypted backup/restore with audit-chain continuity; prevent Q/A content in ordinary logs/crash reports; document who can read restored content. |
| Rationale | User questions may repeat sensitive financial details. Encryption at rest does not resolve lifecycle, restoration, support access, or deletion obligations. |
| Impact / likelihood / severity | Impact **High**; likelihood **Medium**; severity **High**. |
| Packaging blocker | **Yes** while backup/disposal remain retained first-release requirements; otherwise pilot blocker after approved scope change. |
| Pilot blocker | **Yes.** |
| Verification | Retention-boundary tests; review/period/all-data disposal; backup/restore on replacement Windows machine; audit sequence/seal verification; plaintext scan of logs/temp/crash artifacts. |
| Suggested owner | Data Governance and Persistence Lead |

### RR-14 — Enterprise deployment and support operations are undefined

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | No validated Intune/SCCM silent-install command, MSI detection rule, service identity, firewall package, offline model provisioning process, support bundle, health diagnostic, or help-desk runbook exists. NFR-054 is only partially complete for installer/runtime/model repair. |
| Components/files | Packaging ADR; technical implementation plan; distribution documentation; runtime/configuration code; traceability matrix |
| Required action | Produce silent install/uninstall and detection contracts; define privilege and service accounts; deliver endpoint policy and offline payload process; add privacy-preserving diagnostics/correlation IDs; write Tier 1–3 repair/escalation runbooks and support-data handling rules. |
| Rationale | A clean local launch is not an operable enterprise pilot. Administrators need repeatable deployment and support without exposing review data. |
| Impact / likelihood / severity | Impact **High**; likelihood **High**; severity **High**. |
| Packaging blocker | No for an engineering candidate; **yes for an enterprise-distributable package**. |
| Pilot blocker | **Yes.** |
| Verification | Intune/SCCM lab deployment to standard-user machines; offline install; upgrade/detection test; support incident drills; diagnostic bundle privacy review. |
| Suggested owner | Endpoint Management and Product Support |

### RR-15 — Governed documentation conflicts with the implemented/release state

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | Several approved requirements/architecture artifacts still show Draft/Proposed or pre-simplification Ask Fin setup language. `docs/DISTRIBUTION.md` describes wheel/zipapp distribution and says native installers were not built. The traceability review records implementation/specification drift and states that packaging must wait for stabilization. |
| Components/files | V2 application architecture, persistence model, ADRs, Ask Fin delta/simplification documents, `docs/DISTRIBUTION.md`, `DEPENDENCIES.md`, traceability matrix |
| Required action | Reconcile normative status and supersession; record the final automatic-readiness/model-pin contract; replace legacy distribution instructions with the approved Windows topology; ensure all “delivered” claims match evidence and all deferred items are explicit. |
| Rationale | Conflicting operational instructions can bypass controls, misstate capabilities, and make review approval non-reproducible. |
| Impact / likelihood / severity | Impact **High**; likelihood **High**; severity **High**. |
| Packaging blocker | **Yes — release instructions and governed baseline must identify one behavior.** |
| Pilot blocker | **Yes.** |
| Verification | Documentation consistency review; requirement-to-code-to-test trace; no contradictory installation/model/security guidance; approved release-readiness record. |
| Suggested owner | Product Architect with SDD Governance Lead |

### RR-16 — Local administrator/malware control remains outside the application boundary

| Field | Assessment |
|---|---|
| Classification | **Should fix** |
| Status | Residual risk requiring explicit acceptance |
| Evidence | FinSight strongly verifies its connection and model identity, but a local administrator or endpoint compromise can replace binaries, alter environment/policy, access an unlocked user session, or control a permitted local process. Application checks cannot establish a trustworthy host by themselves. |
| Components/files | Stage 2 threat model; Windows deployment/security posture; signing and model-digest controls |
| Required action | Document the trusted-host assumption; require supported endpoint protection, least privilege, disk encryption, code/application control, patching, and incident response; bind managed digest/configuration to administrator-controlled policy. |
| Rationale | This is a standard desktop trust boundary, but leaving it implicit overstates “private/local” guarantees. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **Low to Medium** on managed endpoints; severity **High** residual. |
| Packaging blocker | No after controls and trust statement are approved. |
| Pilot blocker | Conditional on enterprise security acceptance. |
| Verification | Threat-model sign-off; endpoint baseline attestation; tamper/application-control drill; residual-risk acceptance with named owner and review date. |
| Suggested owner | Enterprise Security Risk Owner |

### RR-17 — Approved financial rule and status contracts are not correctly implemented

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | Closeout boundary probes show: CORE-04 includes 71 unapproved Budget/formula scopes; optional rule failures can change Overall Review Status; RAG and summary health/count projections violate §2.7; 3+ member duplicate exposure/count is understated; valid GED rows after the selected month are included; and duplicate fingerprint scalar canonicalization is incomplete. The approved permanent IDs are `R-VAL-01..05`, while production persists `CORE-01..05` aliases. |
| Components/files | `src/finsight/domain/financial_validation.py`; rule seed/management and repository code; Stage 1 oracle/script; V2 functional requirements §2.7 and §11–12; consolidated test inventory and traceability matrix |
| Required action | Reconcile protected identity and CORE-04 through governance; implement exact core-only status/RAG/summary policy, selected-period eligibility, duplicate 3+ exposure/count, and typed fingerprint behavior; regenerate the independent oracle and retained-run evidence. |
| Rationale | These defects affect deterministic financial conclusions and the historical identity of protected controls. A visually correct application cannot be packaged while its governing financial contract is wrong. |
| Impact / likelihood / severity | Impact **Critical**; likelihood **High** on boundary data; severity **Critical**. |
| Packaging blocker | **Yes — unconditional.** |
| Pilot blocker | **Yes.** |
| Verification | Positive/negative/boundary contract suite; exact rule/scope/result identity assertions; independently regenerated OOXML/Decimal oracle; historical migration/replay; full clean regression. |
| Suggested owner | Financial Validation Lead with Financial Control Approver and Data Migration Lead |

### RR-18 — Only one Budget/GED layout and external source retention are supported

| Field | Assessment |
|---|---|
| Classification | **Deferred** |
| Status | Accepted limitation only for explicitly prequalified input |
| Evidence | Production extraction supports the approved `SLV-001` Budget and GED layouts. Original source bytes are not copied into the encrypted store; bindings and fingerprints are retained, so stored results remain but raw-row reconstruction can become unavailable if external files are moved or deleted. No broader organization-specific layout catalogue is implemented. |
| Components/files | `src/finsight/infrastructure/slv001_extractor.py`; workbook-safety and source-intake services; ADR-V2-006; source-intake/Stage 1 verification |
| Required action | Publish the exact supported-layout contract and source-retention duty; add preflight/user guidance and an operational retention check. Treat additional layouts as future governed reader versions, not silent schema guessing. |
| Rationale | Layout drift can block intake, and missing external source files can limit later raw-evidence navigation even though sealed results persist. |
| Impact / likelihood / severity | Impact **High**; likelihood **Medium** outside the sample department; severity **Medium** when clearly constrained. |
| Packaging blocker | No, if the supported-layout limitation and retention responsibility are explicit. |
| Pilot blocker | No for a prequalified `SLV-001` pilot; **Yes** for unqualified source variants. |
| Verification | Pilot-file compatibility certification; moved/missing-source reopen tests; clear in-product limitation; governed new-reader contract tests for any later layout. |
| Suggested owner | Product Owner with Data Ingestion Lead and Pilot Operations |

### RR-19 — Native accessibility and large-workbook performance are not qualified

| Field | Assessment |
|---|---|
| Classification | **Must fix before pilot** |
| Status | Open |
| Evidence | The current full suite fails 200% appearance sizing and Settings Back focus; native Windows screen-reader validation remains pending. Approved 10,000-row/performance and standard 8 GB/16 GB laptop expectations do not have representative workbook, long-history, rendering, latency, or memory evidence. |
| Components/files | Desktop theme/components/views; accessibility tests; NFR-001–003, NFR-027, NFR-042, NFR-092; workbook-safety limits; current test inventory |
| Required action | Close the current accessibility regressions before a candidate build, then qualify the frozen Windows application with NVDA/keyboard/high-contrast/DPI journeys and representative maximum-volume workbooks/history on the supported hardware matrix. |
| Rationale | A product can pass small-fixture automation yet become unusable for assistive-technology users or stall on realistic reports. |
| Impact / likelihood / severity | Impact **High**; likelihood **Medium to High**; severity **High**. |
| Packaging blocker | Current automated accessibility failures are already a blocker under RR-01; the full native/performance qualification may follow the engineering candidate. |
| Pilot blocker | **Yes.** |
| Verification | Green scaling/focus tests; recorded NVDA journey; 100–200% DPI/theme/high-contrast matrix; approved ingestion/validation/table/filter/reopen latency and peak resource report. |
| Suggested owner | Accessibility Lead with Desktop and Performance Engineering |

### RR-20 — Required current reports and exports are incomplete

| Field | Assessment |
|---|---|
| Classification | **Must fix before packaging** |
| Status | Open |
| Evidence | The modern Leadership/Review Summary is on-screen, but the approved first-release printable/PDF Review Summary and spreadsheet-compatible Findings, Rule Results, and summarized-financial-data exports are not delivered through the current governed V2 workflow. Legacy JSON/CSV paths do not satisfy the current publication, identity, and accessibility contract. |
| Components/files | V2 functional requirements §2.13; root FR-116–120; legacy `application/export.py` and output/findings views; current `financial_review_view.py`; traceability matrix |
| Required action | After stabilization, implement the approved PDF/print and spreadsheet-compatible outputs from the selected persisted Review Version/Validation Run, including publication/historical labels, exact financial/result identity, evidence references, accessibility, and no UI-side recalculation. |
| Rationale | Leadership-ready output is a stated first-release deliverable. Shipping only an on-screen summary leaves the monthly review workflow and audit handoff incomplete. |
| Impact / likelihood / severity | Impact **High**; likelihood **High**; severity **High**. |
| Packaging blocker | **Yes while these remain approved first-release requirements.** |
| Pilot blocker | **Yes** if the pilot requires the promised leadership/report handoff; otherwise requires explicit Product Owner scope acceptance. |
| Verification | Golden PDF/print and XLSX/CSV content tests; exact run/rule-set/review identity; Decimal totals; accessible structure; reopen/historical labels; independent finance-user review. |
| Suggested owner | Reporting/UX Lead with Financial Validation and Accessibility reviewers |

## 4. Confirmed Ask Fin strengths

These are verified controls, not closure of the risks above:

- plain-HTTP, explicit-port, loopback-only endpoint normalization;
- all DNS answers and the connected peer must resolve to loopback;
- redirect rejection and proxy bypass;
- API path allowlist for tags, model inspection, and chat;
- cloud/remote model alias rejection;
- exact model/profile/SHA-256 verification immediately before each prompt;
- no cloud fallback and no effect on deterministic validation availability;
- current Windows actor authorization and selected-review/run scope rechecked;
- cross-review and cross-scope grounding rejection;
- deterministic refusals for financial decisions before provider invocation;
- structured response, citation, supported-claim, and exact-value verification;
- post-model decision/authority language rejection;
- immutable audit write before a successful answer is returned.

Focused command executed:

```text
.venv/bin/python -m pytest -q \
  tests/ai/test_ollama_provider.py \
  tests/ai/test_ollama_setup_status.py \
  tests/ai/test_private_ask_fin_stage2.py \
  tests/integration/test_private_ask_fin_v2_grounding.py \
  tests/ui/test_stage2_private_ask_fin_dialog.py \
  tests/infrastructure/test_runtime_paths.py \
  tests/infrastructure/test_secure_store.py \
  tests/infrastructure/test_identity.py \
  tests/infrastructure/test_authorization_manifest.py \
  tests/infrastructure/test_authorization_source.py \
  tests/application/test_authorization.py \
  tests/ui/test_packaging.py
```

Result: **204 passed, 2 subtests passed in 2.04 seconds.** This focused pass does
not supersede the red repository-wide result.

## 5. External licensing and runtime references

- [Ollama MIT license](https://github.com/ollama/ollama/blob/main/LICENSE)
- [Ollama Windows installation and storage behavior](https://docs.ollama.com/windows)
- [Ollama FAQ: cloud disablement, binding, and proxy behavior](https://docs.ollama.com/faq)
- [Ollama Llama 3.2 model listing](https://ollama.com/library/llama3.2)
- [Meta Llama 3.2 community license](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE)
- [Qt for Python licensing overview](https://doc.qt.io/qtforpython-6/)
- [Qt for Python commercial considerations](https://doc.qt.io/qtforpython-6.10/commercial/index.html)
- [Qt for Python license inventory](https://doc.qt.io/qtforpython-6/licenses.html)
- [PyInstaller licensing documentation](https://pyinstaller.org/_/downloads/en/v6.5.0/pdf/)
- [WiX Toolset repository and distribution terms](https://github.com/wixtoolset/wix)
- [WiX source license](https://github.com/wixtoolset/wix/blob/main/LICENSE.TXT)
- [SQLCipher Community Edition license guidance](https://www.zetetic.net/sqlcipher/community/)
- [SQLCipher licensing overview](https://www.zetetic.net/sqlcipher/license/)

## 6. Evidence inspected

### Read completely

- `initiatives/configurable-rule-engine-v2/docs/STAGE-2-ASK-FIN-GROUNDING-AND-DECISION-BOUNDARY-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/docs/STAGE-2-ASK-FIN-PROMPT-PACK-1.0.0.md`
- `initiatives/configurable-rule-engine-v2/docs/STAGE-2-LOCAL-INFERENCE-THREAT-MODEL-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/docs/STAGE-2-PRIVATE-ASK-FIN-ARCHITECTURE-DELTA-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/tasks/STAGE-2-GOVERNED-IMPLEMENTATION-PLAN-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/verification/STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/adr/ADR-V2-005-private-engine-bound-ai.md`
- `specs/adr/ADR-009-ai-persistence-and-retention.md`
- `specs/adr/ADR-010-ai-masking-policy.md`
- `initiatives/configurable-rule-engine-v2/adr/ADR-V2-004-windows-packaging-and-support.md`
- `docs/12-build-readiness-runbook.md`
- `docs/DISTRIBUTION.md`
- `DEPENDENCIES.md`
- `initiatives/configurable-rule-engine-v2/verification/DEPENDENCY-QUALIFICATION-2026-07-27.md`
- `initiatives/configurable-rule-engine-v2/adr/ADR-V2-002-sequential-multi-actor-local-governance.md`
- `initiatives/configurable-rule-engine-v2/adr/ADR-V2-003-encrypted-authoritative-persistence-and-recovery.md`
- `initiatives/configurable-rule-engine-v2/adr/ADR-V2-007-ledger-consumers-and-derived-records.md`
- `initiatives/configurable-rule-engine-v2/requirements/MVP-REMEDIATION-DELTA-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/requirements/GOVERNED-V2-DELTA-2026-07-27.md`
- `initiatives/configurable-rule-engine-v2/specs/02-non-functional-requirements.md`
- `initiatives/configurable-rule-engine-v2/plans/TECHNICAL-IMPLEMENTATION-PLAN.md`
- `src/finsight/infrastructure/ai/private_config.py`
- `src/finsight/infrastructure/ai/private_audit.py`
- `src/finsight/infrastructure/ai/providers/ollama.py`
- `src/finsight/delivery/desktop/ask_fin_preferences.py`
- `src/finsight/domain/ai/local_endpoint.py`
- `src/finsight/infrastructure/runtime_paths.py`
- `tests/ai/test_ollama_provider.py`
- `tests/ai/test_ollama_setup_status.py`
- `tests/infrastructure/test_runtime_paths.py`
- `tests/infrastructure/test_secure_store.py`
- `tests/infrastructure/test_identity.py`
- `tests/infrastructure/test_authorization_manifest.py`
- `tests/infrastructure/test_authorization_source.py`
- `tests/application/test_authorization.py`
- `tests/ui/test_packaging.py`

### Inspected by relevant section, symbol, or trace

- `initiatives/configurable-rule-engine-v2/docs/APPLICATION-ARCHITECTURE.md`
- `initiatives/configurable-rule-engine-v2/docs/PERSISTENCE-MODEL.md`
- `initiatives/configurable-rule-engine-v2/specs/01-functional-requirements.md`
- `initiatives/configurable-rule-engine-v2/readiness/closeout-2026-07-29/CONSOLIDATED-TEST-INVENTORY-2026-07-29.md`
- `initiatives/configurable-rule-engine-v2/readiness/closeout-2026-07-29/UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md`
- `src/finsight/application/ai/private_ask_fin.py`
- `src/finsight/application/ai/private_claims.py`
- `src/finsight/application/ai/private_contracts.py`
- `src/finsight/application/ai/private_grounding.py`
- `src/finsight/application/ai/private_prompt.py`
- `src/finsight/app.py`
- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/app.py`
- `src/finsight/infrastructure/secure_store.py`
- `src/finsight/infrastructure/identity.py`
- `src/finsight/infrastructure/authorization_manifest.py`
- `src/finsight/infrastructure/authorization_source.py`
- the focused Ask Fin, authorization, secure-storage, and UI test files listed in
  the executed command

No production code or test code was modified by this review.
