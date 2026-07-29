# FinSight V2 Windows Packaging Readiness Checklist

**Date:** 2026-07-29
**Scope:** Windows executable/MSI, Ask Fin local runtime/model, security, licensing,
deployment, recovery, and release operations
**Current gate:** **NOT READY — do not begin release packaging**

This is an evidence checklist, not a statement that an item is complete. A box may be
checked only when the named verification artifacts exist for the same immutable release
commit. Source/module launch tests do not qualify a frozen application or installer.

## 1. Gate summary

| Gate | State | Blocks packaging | Blocks pilot |
|---|---:|---:|---:|
| PKG-01 Stable, immutable release baseline | Open | Yes | Yes |
| PKG-02 Approved package and AI-runtime topology | Open | Yes | Yes |
| PKG-03 Reproducible frozen application build | Open | Yes | Yes |
| PKG-04 Governed MSI and application resources | Open | Yes | Yes |
| PKG-05 License, SBOM, and notices approval | Open | Yes | Yes |
| PKG-06 Signing, provenance, and artifact integrity | Open | Yes | Yes |
| PKG-07 Windows-native security qualification | Open | Yes | Yes |
| PKG-08 Ask Fin model identity and egress enforcement | Open | Conditional | Yes |
| PKG-09 Ask Fin resource and performance qualification | Open | Conditional | Yes |
| PKG-10 Install/repair/upgrade/rollback/uninstall matrix | Open | Yes | Yes |
| PKG-11 Backup, restore, retention, and disposal | Open | Yes | Yes |
| PKG-12 Enterprise deployment and first-run readiness | Open | No* | Yes |
| PKG-13 Accessibility and standard-user qualification | Open | Yes | Yes |
| PKG-14 Support, diagnostics, and incident operations | Open | No* | Yes |
| PKG-15 Final release evidence and authorization | Open | Yes | Yes |

\*PKG-12 and PKG-14 do not block creation of an engineering-only installer candidate,
but they block labeling or distributing it as an enterprise pilot package.

## 2. Detailed checklist

### PKG-01 — Stabilize and freeze one release baseline

- [ ] All material financial, architecture, accessibility, and UI order-dependence
  defects in the closeout inventory are resolved.
- [ ] Complete test, financial-oracle, architecture/import, static, and dependency
  suites pass from one clean commit.
- [ ] The worktree is clean and the commit/tag is recorded in the release manifest.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | Full suite is **4 failed, 1,212 passed, 2 subtests passed**; material closeout defects and a large uncommitted worktree remain. |
| Components/files | `CONSOLIDATED-TEST-INVENTORY-2026-07-29.md`; `UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md`; release Git state |
| Action | Close material findings, reconcile governed rule/financial behavior, commit the exact candidate, and rerun all release gates. |
| Rationale / risk | An unstable or moving source state makes a binary, signature, SBOM, and audit claim irreproducible. Impact **Critical**; likelihood **High**; severity **Critical**. |
| Verification evidence required | Clean CI report tied to commit SHA; financial oracle; import-linter/architecture pass; dependency audit; clean `git status`; independent stabilization verdict. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Application Engineering Lead and QA Lead |

### PKG-02 — Approve one Windows package and Ask Fin topology

- [ ] Record whether Ollama/model are automatically provisioned by the FinSight
  installer or by one coordinated enterprise deployment dependency.
- [ ] Define per-machine/per-user install scope, service identity, model/cache
  ownership, privileges, offline behavior, and first-run experience.
- [ ] Prove that an end user never uses a terminal, downloads a model manually, or
  starts Ollama manually.
- [ ] Update the packaging ADR and supersede conflicting legacy distribution guidance.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | FinSight detects but does not install/start/repair Ollama or download its model. Official Ollama Windows defaults are predominantly per-user and auto-updating, while FinSight supports shared governed machine data. |
| Components/files | `ADR-V2-004-windows-packaging-and-support.md`; `docs/DISTRIBUTION.md`; Ask Fin configuration/composition; Windows architecture documents |
| Action | Select either installer-owned provisioning or a coordinated enterprise package that automatically installs/configures the exact runtime and model. A manually satisfied prerequisite does not meet the approved one-click/no-terminal release criterion. Govern every lifecycle/security consequence. |
| Rationale / risk | Installer contents, size, privileges, cache location, service ownership, support, licensing, and offline behavior otherwise remain undefined. Impact **Critical**; likelihood **High**; severity **Critical**. |
| Verification evidence required | Accepted ADR/delta; package bill of materials; first-run state diagram; multi-actor design; offline automatic-provisioning plan; clean-machine no-terminal/no-manual-start usability proof. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Solution Architect with Windows Platform, Security, and Legal |

### PKG-03 — Build the application reproducibly as a frozen Windows executable

- [ ] Create and pin the PyInstaller or approved equivalent build specification.
- [ ] Collect all Python, PySide6/Qt, QtAwesome, SQLCipher, migration, theme, icon,
  and configuration resources explicitly.
- [ ] Build only on a controlled Windows release runner from the frozen commit.
- [ ] Prove two controlled builds produce the expected reproducible manifest/hashes.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | No frozen executable specification or Windows binary exists. `tests/ui/test_packaging.py` launches the importable source application only. |
| Components/files | Planned build spec; `pyproject.toml`; `requirements*.txt`; desktop/resources/migrations; `tests/ui/test_packaging.py` |
| Action | Implement a deterministic freeze pipeline with pinned tools, hidden-import/resource declarations, artifact manifest, and frozen-app smoke tests. |
| Rationale / risk | Source success does not prove frozen imports, plugins, DLLs, SQLCipher, Qt resources, or migrations. Impact **Critical**; likelihood **High**; severity **Critical**. |
| Verification evidence required | Controlled build logs; EXE hash/manifest; launch without Python/source; resource/theme/migration/database/Ask Fin-unavailable smoke tests; no unexpected DLL search path. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Build/Release Engineering |

### PKG-04 — Produce a governed MSI

- [ ] Create pinned WiX source with explicit Product/Upgrade codes, feature layout,
  install scope, directories, shortcuts, ARP metadata, and failure rollback.
- [ ] Define install prerequisites and enforce them without ad hoc downloads.
- [ ] Prevent MSI custom actions from logging secrets or financial content.
- [ ] Validate silent and interactive installation.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | FR-175 and NFR-094 are Not Started; no WiX source or MSI exists. |
| Components/files | Planned WiX project; packaging ADR; runtime path/security adapters; build pipeline |
| Action | Implement the MSI using an exact approved WiX version and terms; make install/rollback deterministic and privilege-minimal. |
| Rationale / risk | The required distribution artifact and its Windows lifecycle contract are absent. Impact **Critical**; likelihood **High**; severity **Critical**. |
| Verification evidence required | ICE/installer validation; standard and silent install; launch from installed location; rollback on injected failure; no source/runtime prerequisite leakage. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Windows Installer Engineering |

### PKG-05 — Complete license, SBOM, and notice approval

- [ ] Enumerate every frozen/runtime dependency and exact version/license.
- [ ] Decide and approve Qt commercial versus LGPL-compliant posture.
- [ ] Include SQLCipher, PyInstaller, Python, Qt, fonts/icons, and other notices.
- [ ] Approve the exact WiX build/distribution terms.
- [ ] Decide whether Ollama and the Llama 3.2 model are redistributed and satisfy
  their separate licenses and attribution obligations.
- [ ] Include an SPDX or CycloneDX SBOM and accessible Third-Party Notices.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | Dependency documentation exists but no counsel-approved frozen-binary inventory or notice bundle exists. Ollama is MIT; the default Meta Llama model uses a separate custom community license. |
| Components/files | `DEPENDENCIES.md`; `requirements*.txt`; `pyproject.toml`; build output; Ollama/model payload; Third-Party Notices |
| Action | Reconcile the exact build SBOM with legal obligations and obtain distribution approval before finalizing payloads. |
| Rationale / risk | Development dependency use does not establish redistribution rights or required notices. Impact **High**; likelihood **High**; severity **High**. |
| Verification evidence required | Counsel/OSPO sign-off; SBOM-to-binary and SBOM-to-notice reconciliation; automated notice-presence check; user-accessible license screen/file. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Legal/OSPO with Release Engineering |

### PKG-06 — Sign, timestamp, attest, and scan release artifacts

- [ ] Establish protected certificate access and a two-person release process.
- [ ] Authenticode-sign and RFC 3161 timestamp the EXE and MSI.
- [ ] Generate checksums, provenance/attestation, SBOM, and release manifest.
- [ ] Run malware and dependency/vulnerability scans on the final signed payload.
- [ ] Test that tampering invalidates verification.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | FR-178/NFR-095 are Not Started; no signing, provenance, final SBOM, malware, or tamper evidence exists. |
| Components/files | Release pipeline; PKI/HSM or approved signing service; EXE/MSI; release manifest/SBOM |
| Action | Implement the controlled signing and integrity pipeline after all payloads are final. |
| Rationale / risk | Administrators cannot verify publisher, content, or custody of unsigned/unattested financial software. Impact **High**; likelihood **High**; severity **High**. |
| Verification evidence required | `Get-AuthenticodeSignature`/equivalent trust on clean Windows; valid timestamp after signing certificate expiry simulation; hashes; attestation; scan reports; tamper-negative test. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Release Engineering and Security/PKI |

### PKG-07 — Qualify Windows-native identity, encryption, and authorization

- [ ] Verify Windows SID extraction and actor continuity for at least two users.
- [ ] Verify DPAPI key protection and SQLCipher encryption in the installed app.
- [ ] Apply and test explicit ACLs on program, data, backup, log, temp, and model paths.
- [ ] Prove ordinary users cannot modify governed authorization/model policy.
- [ ] Scan disk, process artifacts, logs, crash files, and temp files for plaintext
  secrets and review/Ask Fin content.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | Adapters and unit/security tests exist, but frozen native Windows SID/DPAPI/ACL/SQLCipher behavior is not qualified. |
| Components/files | `identity.py`; `secure_store.py`; `runtime_paths.py`; authorization adapters; encrypted persistence; Windows MSI configuration |
| Action | Execute a native installed security matrix under standard users, multiple actors, and administrator tamper attempts. |
| Rationale / risk | POSIX and unfrozen tests cannot prove Windows API, ACL, DLL, or packaged secret behavior. Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Verification evidence required | SID/ACL/DPAPI evidence; encrypted-file inspection; unauthorized actor/tamper denial; DLL loading trace; plaintext scan; security review sign-off. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Security Engineering and Windows Platform Engineering |

### PKG-08 — Enforce Ask Fin model identity and private processing

- [ ] Provision an administrator-controlled exact model digest/profile.
- [ ] Fail closed across restarts on absent, changed, or unverifiable identity.
- [ ] Disable Ollama cloud behavior and bind the daemon only to loopback.
- [ ] Apply endpoint firewall/application-control policy that blocks daemon egress
  and unauthorized inbound access.
- [ ] Keep FinSight redirect rejection, proxy bypass, peer-loopback validation,
  path allowlisting, authorization rechecks, grounded claims, decision refusals,
  and fail-closed audit behavior.

| Field | Requirement |
|---|---|
| Classification | **Must fix before pilot** |
| Evidence today | Strong application controls are tested, but the default pin is first-observed per provider session and the daemon's own cloud/egress/update posture is not deployment-enforced. |
| Components/files | `providers/ollama.py`; `private_config.py`; `ask_fin_preferences.py`; `local_endpoint.py`; threat model; endpoint policy |
| Action | Replace pilot TOFU with managed immutable identity and control the complete local provider process boundary. |
| Rationale / risk | A wrong first-observed service/model or egress-capable daemon can undermine the promised private/local boundary. Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Verification evidence required | Restart/mismatch/tamper tests; network capture with zero non-loopback traffic; cloud disabled diagnostic; firewall/listener assertions; exact digest in audit/release manifest. |
| Blockers | Packaging **Conditional if Ask Fin is enabled**; pilot **Yes**. |
| Suggested owner | Security Engineering and AI Runtime Owner |

### PKG-09 — Bound Ask Fin resources and qualify supported hardware

- [ ] Set governed maximum output tokens and response bytes.
- [ ] Enforce service-level concurrency, queue/full behavior, cancellation, and
  recovery independently of the UI.
- [ ] Test slow, oversized, malformed, parallel, and unavailable provider behavior.
- [ ] Benchmark cold/warm inference and peak resources on supported Windows 11
  8 GB and 16 GB systems.
- [ ] Define disk headroom, latency targets, and graceful feature disablement.

| Field | Requirement |
|---|---|
| Classification | **Must fix before pilot** |
| Evidence today | Timeouts and UI Send disabling exist, but response `read()` is unbounded, the output-token cap may be omitted, and no authoritative concurrency semaphore is present. No target-hardware benchmark exists for the approximately 2 GB default model. |
| Components/files | `providers/ollama.py`; `private_config.py`; `private_ask_fin.py`; Ask Fin dialog/controller; performance NFRs |
| Action | Add hard resource limits and complete the native performance/availability matrix. |
| Rationale / risk | A local service can exhaust memory/CPU, stall the UI, or behave differently on minimum hardware. Impact **High**; likelihood **Medium to High**; severity **High**. |
| Verification evidence required | Adversarial provider tests; concurrency/cancel tests; peak resource report; cold/warm latency; low-disk/low-memory behavior; support matrix. |
| Blockers | Packaging **Conditional if Ask Fin ships enabled**; pilot **Yes when Ask Fin is in scope**. |
| Suggested owner | AI Runtime and Performance Engineering |

### PKG-10 — Pass the complete installer lifecycle matrix

- [ ] Test clean install for standard user and administrator-mediated enterprise
  deployment.
- [ ] Test launch, repair, same-version reinstall, in-place upgrade, failed-upgrade
  rollback, downgrade policy, and uninstall.
- [ ] Test install and upgrade with an existing encrypted database, audit history,
  authorization manifest, model cache, and appearance/preferences.
- [ ] Define and verify which user data/model assets uninstall retains or removes.
- [ ] Run power-loss and process-kill fault injection at critical lifecycle points.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | FR-177/NFR-094 remain Not Started; no MSI lifecycle evidence exists. |
| Components/files | MSI/WiX project; migrations; runtime paths; SQLCipher persistence; authorization store; Ask Fin preferences/model topology |
| Action | Execute the matrix on disposable clean Windows VMs with preserved evidence and rollback assertions. |
| Rationale / risk | Upgrades and repairs can corrupt or orphan authoritative financial/audit data even when a clean install works. Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Verification evidence required | Timestamped VM matrix; before/after hashes/schema/audit continuity; rollback logs; retained/removed data assertions; no manual terminal repair. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Release Engineering with Persistence Lead |

### PKG-11 — Implement and qualify backup, restore, retention, and disposal

- [ ] Implement or govern out of first-release scope the approved complete backup
  and replacement-machine restore obligation.
- [ ] Preserve review, rule-set/run/result, finding, audit, authorization/registry,
  and Ask Fin history continuity.
- [ ] Define AI question/answer retention and legal-hold behavior.
- [ ] Verify review, period, and all-data disposal, including backups and keys.
- [ ] Ensure ordinary logs/support bundles never contain raw Ask Fin content.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** while retained as first-release scope |
| Evidence today | NFR-101 and user backup/restore are Not Started; raw Q/A are encrypted and audit-integrity protected, but portable recovery and full lifecycle controls are absent. |
| Components/files | Persistence model; ADR-V2-003; ADR-009/010; AI audit adapter; review disposal; authorization registry |
| Action | Deliver the governed recovery/lifecycle feature or obtain an approved scope change before packaging. |
| Rationale / risk | Authoritative financial and AI/audit history may be lost, stranded, or retained contrary to policy. Impact **Critical**; likelihood **Medium**; severity **Critical**. |
| Verification evidence required | Encrypted backup; replacement-machine restore; audit/seal/registry continuity; retention-boundary tests; disposal and plaintext-remnant scans; recovery runbook. |
| Blockers | Packaging **Yes unless formally descoped**; pilot **Yes**. |
| Suggested owner | Persistence Lead and Data Governance |

### PKG-12 — Prove enterprise deployment and first-run behavior

- [ ] Provide documented quiet install/uninstall switches, return codes, and MSI
  detection rules for Intune/SCCM.
- [ ] Test offline installation or the approved managed prerequisite path.
- [ ] Apply firewall, service, configuration, model-digest, and update policies.
- [ ] Launch successfully as a standard user with no terminal or developer tools.
- [ ] Present clear non-blocking behavior when Ask Fin is unavailable.

| Field | Requirement |
|---|---|
| Classification | **Must fix before pilot** |
| Evidence today | No validated enterprise deployment profile, offline model process, endpoint policy bundle, or standard-user first-run package evidence exists. |
| Components/files | MSI; Intune/SCCM metadata/scripts; Windows endpoint policies; Ask Fin status/UI; first-run/support documentation |
| Action | Package and test the complete managed deployment profile in an endpoint-management lab. |
| Rationale / risk | Manual engineering installation does not scale and can produce inconsistent security/model/runtime posture. Impact **High**; likelihood **High**; severity **High**. |
| Verification evidence required | Intune/SCCM deployment logs; detection/upgrade success; offline scenario; standard-user screenshots/video; configuration/policy attestation. |
| Blockers | Packaging **No for engineering candidate; yes for enterprise-labeled package**; pilot **Yes**. |
| Suggested owner | Endpoint Management |

### PKG-13 — Qualify accessibility, themes, scaling, and standard-user UX in the installed build

- [ ] Resolve the current 200% clipping, Settings focus, and Ask Fin drawer
  order-dependence defects.
- [ ] Test keyboard-only operation, screen-reader names/announcements, focus order,
  100–200% text scaling, zoom/resizing, light/dark/system modes, and high contrast.
- [ ] Test on the actual frozen application and supported Windows display scales.
- [ ] Confirm errors and status use text/icon semantics, not color alone.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** |
| Evidence today | Current full suite includes accessibility/UI failures; native screen-reader qualification remains pending. |
| Components/files | desktop shell/views/theme/components; accessibility and appearance tests; installed EXE |
| Action | Fix material defects and complete the native Windows assistive-technology matrix. |
| Rationale / risk | Automated offscreen/source tests do not prove installed native focus, announcement, DPI, or animation behavior. Impact **High**; likelihood **High** for affected users; severity **High**. |
| Verification evidence required | Green automated tests; NVDA or approved screen-reader script/results; 100/125/150/200% DPI screenshots; keyboard journey; high-contrast/theme evidence. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Desktop UX/Accessibility Lead |

### PKG-14 — Establish support, diagnostics, update, and incident operations

- [ ] Pin supported FinSight/Ollama/model combinations and disable uncontrolled
  runtime/model updates.
- [ ] Define staged update ring, compatibility test, repair, and rollback.
- [ ] Provide privacy-preserving health diagnostics and support bundle.
- [ ] Write Tier 1–3 runbooks for install, encrypted-store, identity/authorization,
  migration, provider, model mismatch, performance, and recovery failures.
- [ ] Define incident response and support access rules for financial/Ask Fin data.

| Field | Requirement |
|---|---|
| Classification | **Must fix before pilot** |
| Evidence today | App diagnostics exist, but installer/runtime/model repair and enterprise operations are not delivered; Ollama can auto-update and model-cache ownership is undefined. |
| Components/files | release manifest; update policy; diagnostics; support runbooks; Ollama/model deployment |
| Action | Create a supported-version matrix and exercise representative support incidents before user deployment. |
| Rationale / risk | An update or support action can break Ask Fin, expose sensitive data, or leave users without a recoverable path. Impact **High**; likelihood **High**; severity **High**. |
| Verification evidence required | Update/rollback drill; corrupt/missing/mismatch runtime incidents; sanitized support bundle review; escalation rehearsal; service-level owner/on-call assignment. |
| Blockers | Packaging **No for engineering candidate; yes for enterprise-labeled package**; pilot **Yes**. |
| Suggested owner | Product Support and Release Engineering |

### PKG-15 — Conduct final release review and authorize distribution

- [ ] Reconcile requirements, architecture/ADRs, distribution, privacy/security,
  support, and user documentation to the implemented release.
- [ ] Attach every PKG-01–PKG-14 artifact to one release evidence index.
- [ ] Perform one independent security/privacy review and one independent
  release/install review on the signed candidate.
- [ ] Record residual risks, owners, expiration/review dates, and approvals.
- [ ] Obtain the required Final Product and Windows Packaging and Release approvals.

| Field | Requirement |
|---|---|
| Classification | **Must fix before packaging** (final release gate) |
| Evidence today | Several governed artifacts retain Draft/Proposed or legacy behavior; no signed candidate or complete release-evidence set exists. |
| Components/files | Requirements/traceability; architecture/ADRs; risk register; this checklist; signed artifacts; test/security/license/support evidence |
| Action | Review only the immutable signed candidate and publish a single approval record that identifies its hashes, versions, and residual risks. |
| Rationale / risk | Separate passing artifacts do not establish that the exact distributed binary satisfies the approved product contract. Impact **Critical**; likelihood **High without gate**; severity **Critical**. |
| Verification evidence required | Independent PASS verdicts; complete evidence index; approval signatures/actors/timestamps; exact EXE/MSI/SBOM hashes; no unresolved packaging or pilot blocker. |
| Blockers | Packaging **Yes**; pilot **Yes**. |
| Suggested owner | Release Authority, Financial Control Approver, Security, and Product Owner |

## 3. Minimum clean-Windows test matrix

The following matrix is mandatory evidence for PKG-07, PKG-10, PKG-12, and PKG-13.

| Dimension | Minimum coverage |
|---|---|
| Operating system | Supported Windows 11 releases, fully patched |
| Hardware | 8 GB RAM minimum class and 16 GB RAM standard class; CPU-only plus each supported GPU path |
| Actor | Standard user; administrator-mediated install; two distinct Windows users/SIDs |
| Install state | Clean; existing prior release; damaged install; interrupted upgrade |
| Connectivity | Online; offline; proxy-configured OS; outbound-denied endpoint |
| Ask Fin | Provider absent; approved provider/model; wrong digest; changed digest; cloud disabled; slow; oversized; unavailable |
| Data | New empty store; populated encrypted store; backup restore; migration from supported prior schema |
| Display/accessibility | 100%, 125%, 150%, 200%; keyboard-only; screen reader; light/dark/system/high contrast |
| Lifecycle | Install; launch; repair; upgrade; rollback; uninstall; reinstall; replacement-machine restore |

## 4. Exit rule

Packaging readiness is **PASS** only when:

1. every packaging blocker is checked with linked evidence;
2. the exact signed release candidate passes the full clean-Windows matrix;
3. all pilot blockers are either closed or the affected capability is explicitly
   disabled and governed out of pilot scope;
4. the independent release review returns PASS;
5. the approval record names the candidate hashes, SBOM, rule/product version,
   residual risks, and authorized approvers.

Until then, FinSight may continue as a development build, but it must not be described
as a production-ready, enterprise-pilot-ready, or Windows-packaged release.
