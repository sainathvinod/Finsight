# ADR-V2-002 — Sequential Multi-Actor Local Governance and Replaceable Identity

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; Software Architect; Security Architect; Finance Control Owner
- **Partially supersedes:** Root ADR-013 single-user/no-identity assumption
- **Preserves:** One local desktop application, one embedded database, one active application instance per store, and no shared-network database
- **Related contract:** AC-02

## Context

The V2 requirements introduce Reviewer, Rule Administrator, and Financial Control Approver roles. Protected baseline changes require a requester and a different approver. A one-person-per-installation model cannot satisfy that control, but a concurrent multi-user server product is outside MVP scope.

## Decision

One FinSight installation will support multiple authenticated operating-system actors using the same machine-scoped local workspace **sequentially**, never concurrently.

The application retains:

- one PySide6 desktop process;
- one machine-local embedded store;
- one exclusive application lock per store;
- no network-share database;
- no simultaneous sessions or network/background approval service; a signed local scheduler helper may execute only an already-approved immutable future-dated activation; and
- no application-managed passwords.

The MVP identity provider resolves the authenticated Windows account to:

- canonical Actor ID `WINDOWS_ACCOUNT:<SID>`;
- domain-qualified account name;
- identity-source ID and version; and
- resolution timestamp.

Display names are never authorization keys. Identity resolution is an application port. A supported non-Windows adapter and a future Azure AD, Active Directory, or SSO adapter must map to the same canonical Actor contract without changing the rule engine, policy model, or audit schema.

Authorization is policy-as-data outside the rule engine. The MVP permission vocabulary is stable and role definitions are versioned mappings over that vocabulary. This permits additional roles without changing evaluator code.

Role Assignments are delivered through a deployment-admin-managed, signed authorization manifest outside the FinSight UI. The manifest contains:

- manifest schema/version and fingerprint;
- provider-qualified stable Actor IDs;
- role IDs;
- effective-from and optional effective-through timestamps;
- assigning Actor ID/time and assignment version; and
- signature/key identity.

The application validates the manifest signature and schema at startup and before privileged commits. It never offers role assignment or self-elevation. A missing, invalid, expired, or untrusted authorization source fails closed.

Multiple effective roles grant the union of ordinary permissions. Explicit denials always take precedence:

- no actor may approve or reject its own protected request;
- no actor may approve its own role assignment;
- lifecycle gates cannot be bypassed;
- historical evidence cannot be rewritten; and
- FinSight roles grant no spending, invoice, journal, or other financial approval authority.

Every sensitive read and every attempted privileged action records the provider-qualified Actor ID, identity source, policy/assignment version, evaluation time, decision, object/action, and correlation ID. Authorization is enforced at the application service boundary and rechecked inside the persistence transaction for protected commits.

## Consequences

### Positive

- Two-person protected governance is possible without adding a server product.
- The rule engine remains independent of operating-system identity.
- Enterprise authentication can replace the MVP provider behind a port.
- Versioned role policy and assignment evidence make historical authorization reproducible.

### Costs and limitations

- Actors must use the same governed machine sequentially for the MVP.
- Role provisioning requires deployment/IT administration outside FinSight.
- Remote or concurrent approvals require a later server-backed deployment.
- Machine data ACLs and the exclusive lock become release-critical controls.
- Future-dated activation requires a signed OS-scheduled wake plus fail-closed overdue reconciliation; the helper has no approval authority.

## Rejected alternatives

- **Keep `local-user`:** cannot prove requester/approver separation.
- **Store role assignments in editable application settings:** permits self-elevation.
- **Per-user isolated databases:** prevents shared protected-change queues and baseline governance.
- **Build a web/API collaboration service now:** exceeds MVP scope and would create a second deployment architecture.

## Verification

- Windows SID and substitute-provider conformance tests.
- Full permission matrix for all three roles and a configured fourth test role.
- Multi-role self-approval denial tests at UI, application, and commit boundaries.
- Invalid/tampered/expired role-manifest fail-closed tests.
- Sequential actor handoff and second-instance refusal tests.
- Future-dated activation tests with app open, app closed, machine-off/missed wake, lock contention, tampered task, and overdue startup.
- Audit reconstruction proves the policy version and Actor ID used for every decision.

## Approval effect

If accepted, this ADR amends ADR-013 only as stated. It does not authorize concurrent sessions, a network database, or application implementation.
