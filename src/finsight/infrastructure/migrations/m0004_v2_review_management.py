# Implements: V2 FR-123/124/195/197, NFR-082/090, ADR-V2-002/003 — Workflow 1 schema.
from __future__ import annotations

import calendar
import hashlib
import sqlite3

VERSION = 4
NAME = "v2_review_management"


_APPEND_ONLY_TABLES = (
    "v2_store_security_profiles",
    "v2_actor_snapshots",
    "v2_review_cycles",
    "v2_working_candidates",
    "v2_review_disposition_events",
    "v2_review_status_events",
    "v2_review_create_requests",
    "v2_authorization_manifest_snapshots",
    "v2_authorization_role_snapshots",
    "v2_authorization_assignment_snapshots",
    "v2_authorization_manifest_import_events",
    "v2_authorization_decision_events",
    "v2_diagnostic_events",
    "v2_audit_events",
    "v2_audit_event_scopes",
    "v2_generation_analytical_state_events",
)


def _append_only_triggers(conn, table: str) -> None:
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'append_only'); END"
    )
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'append_only'); END"
    )


def _ensure_column(conn, table: str, column: str, declaration: str) -> None:
    existing = {
        row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


def up(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_store_security_profiles("
        "profile_id TEXT PRIMARY KEY, cipher_version TEXT NOT NULL, cipher_page_size INTEGER NOT NULL, "
        "kdf_iterations INTEGER NOT NULL, hmac_algorithm TEXT NOT NULL, kdf_algorithm TEXT NOT NULL, "
        "journal_mode TEXT NOT NULL, synchronous_mode TEXT NOT NULL, binding_name TEXT NOT NULL, "
        "binding_version TEXT NOT NULL, introduced_schema_version INTEGER NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_store_security_profile_head("
        "singleton INTEGER PRIMARY KEY CHECK(singleton=1), profile_id TEXT NOT NULL "
        "REFERENCES v2_store_security_profiles(profile_id))"
    )
    profile = (
        "SQLCIPHER-4.12.0-COMMUNITY-001",
        "4.12.0 community",
        4096,
        256000,
        "HMAC_SHA512",
        "PBKDF2_HMAC_SHA512",
        "wal",
        "FULL",
        "sqlcipher3",
        "0.6.2",
        VERSION,
    )
    conn.execute(
        "INSERT OR IGNORE INTO v2_store_security_profiles(profile_id,cipher_version,"
        "cipher_page_size,kdf_iterations,hmac_algorithm,kdf_algorithm,journal_mode,"
        "synchronous_mode,binding_name,binding_version,introduced_schema_version) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        profile,
    )
    observed = conn.execute(
        "SELECT profile_id,cipher_version,cipher_page_size,kdf_iterations,hmac_algorithm,"
        "kdf_algorithm,journal_mode,synchronous_mode,binding_name,binding_version,"
        "introduced_schema_version FROM v2_store_security_profiles WHERE profile_id=?",
        (profile[0],),
    ).fetchone()
    if observed != profile:
        raise sqlite3.IntegrityError("qualified store security profile mismatch")
    conn.execute(
        "INSERT OR IGNORE INTO v2_store_security_profile_head(singleton,profile_id) VALUES(1,?)",
        (profile[0],),
    )
    if conn.execute(
        "SELECT profile_id FROM v2_store_security_profile_head WHERE singleton=1"
    ).fetchone() != (profile[0],):
        raise sqlite3.IntegrityError("active store security profile mismatch")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_actor_snapshots("
        "actor_id TEXT NOT NULL, snapshot_version INTEGER NOT NULL, display_name TEXT NOT NULL, "
        "identity_source TEXT NOT NULL, captured_at TEXT NOT NULL, "
        "PRIMARY KEY(actor_id, snapshot_version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_cycles("
        "review_id TEXT PRIMARY KEY REFERENCES cycles(cycle_id), selected_month INTEGER NOT NULL "
        "CHECK(selected_month BETWEEN 1 AND 12), selected_year INTEGER NOT NULL "
        "CHECK(selected_year BETWEEN 1000 AND 9999), creation_actor_id TEXT NOT NULL, "
        "creation_actor_display TEXT NOT NULL, identity_source TEXT NOT NULL, created_at TEXT NOT NULL, "
        "origin TEXT NOT NULL CHECK(origin IN ('NATIVE','LEGACY_SNAPSHOT')))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_working_candidates("
        "candidate_id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "predecessor_generation_id TEXT, creation_trigger TEXT NOT NULL, extractor_profile_id TEXT NOT NULL, "
        "creator_actor_id TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(review_id, candidate_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_cycle_pointers("
        "review_id TEXT PRIMARY KEY REFERENCES v2_review_cycles(review_id), active_candidate_id TEXT, "
        "working_generation_id TEXT, published_generation_id TEXT, current_rule_set_id TEXT, "
        "revision INTEGER NOT NULL CHECK(revision >= 0), "
        "FOREIGN KEY(active_candidate_id) REFERENCES v2_working_candidates(candidate_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_disposition_events("
        "event_id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "sequence INTEGER NOT NULL CHECK(sequence > 0), disposition TEXT NOT NULL "
        "CHECK(disposition IN ('Active','Abandoned')), actor_id TEXT NOT NULL, occurred_at TEXT NOT NULL, "
        "reason TEXT NOT NULL, UNIQUE(review_id, sequence))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_status_events("
        "event_id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "owner_kind TEXT NOT NULL CHECK(owner_kind IN ('WorkingCandidate','ReviewGeneration')), "
        "owner_id TEXT NOT NULL, sequence INTEGER NOT NULL CHECK(sequence > 0), previous_status TEXT, "
        "status TEXT NOT NULL CHECK(status IN ('Draft','Data Uploaded','Data Reviewed',"
        "'Validation Complete','Reviewed','Closed','Archived')), actor_id TEXT NOT NULL, "
        "occurred_at TEXT NOT NULL, reason TEXT NOT NULL, "
        "origin TEXT NOT NULL CHECK(origin IN ('NATIVE','LEGACY_SNAPSHOT')), "
        "UNIQUE(owner_kind, owner_id, sequence))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_status_review "
        "ON v2_review_status_events(review_id, occurred_at, sequence)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_create_requests("
        "idempotency_key TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "request_hash TEXT NOT NULL, actor_id TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_authorization_manifest_state("
        "singleton INTEGER PRIMARY KEY CHECK(singleton=1), manifest_version INTEGER NOT NULL, "
        "manifest_hash TEXT NOT NULL, key_id TEXT NOT NULL, accepted_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_authorization_manifest_snapshots("
        "manifest_fingerprint TEXT PRIMARY KEY, manifest_version INTEGER NOT NULL UNIQUE "
        "CHECK(manifest_version>0), schema_version TEXT NOT NULL, key_id TEXT NOT NULL, "
        "canonical_manifest BLOB NOT NULL, detached_signature BLOB NOT NULL, "
        "issued_at TEXT NOT NULL, effective_from TEXT NOT NULL, expires_at TEXT NOT NULL, "
        "role_policy_version TEXT NOT NULL, accepted_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_authorization_role_snapshots("
        "manifest_fingerprint TEXT NOT NULL REFERENCES "
        "v2_authorization_manifest_snapshots(manifest_fingerprint), role_name TEXT NOT NULL, "
        "is_mvp INTEGER NOT NULL CHECK(is_mvp IN (0,1)), permissions_json TEXT NOT NULL, "
        "PRIMARY KEY(manifest_fingerprint,role_name))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_authorization_assignment_snapshots("
        "manifest_fingerprint TEXT NOT NULL REFERENCES "
        "v2_authorization_manifest_snapshots(manifest_fingerprint), ordinal INTEGER NOT NULL "
        "CHECK(ordinal>0), assignment_id TEXT NOT NULL, actor_id TEXT NOT NULL, "
        "actor_source TEXT NOT NULL, allow_roles_json TEXT NOT NULL, deny_roles_json TEXT NOT NULL, "
        "allow_permissions_json TEXT NOT NULL, deny_permissions_json TEXT NOT NULL, "
        "effective_from TEXT NOT NULL, effective_through TEXT, assigning_actor_id TEXT NOT NULL, "
        "assigned_at TEXT NOT NULL, assignment_version INTEGER NOT NULL CHECK(assignment_version>0), "
        "PRIMARY KEY(manifest_fingerprint,assignment_id), "
        "UNIQUE(manifest_fingerprint,ordinal))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_authorization_manifest_import_events("
        "event_id TEXT PRIMARY KEY, manifest_fingerprint TEXT NOT NULL UNIQUE REFERENCES "
        "v2_authorization_manifest_snapshots(manifest_fingerprint), manifest_version INTEGER NOT NULL, "
        "key_id TEXT NOT NULL, prior_manifest_version INTEGER, prior_manifest_fingerprint TEXT, "
        "accepted_at TEXT NOT NULL, accepted_by_actor_id TEXT NOT NULL, "
        "outcome TEXT NOT NULL CHECK(outcome='ACCEPTED'))"
    )
    _ensure_column(
        conn,
        "v2_authorization_manifest_import_events",
        "accepted_by_actor_id",
        "TEXT NOT NULL DEFAULT 'legacy-system'",
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_authorization_decision_events("
        "event_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, permission TEXT NOT NULL, resource_type TEXT, "
        "resource_id TEXT, decision TEXT NOT NULL CHECK(decision IN ('ALLOW','DENY')), "
        "policy_version TEXT NOT NULL, manifest_version INTEGER, reason_code TEXT NOT NULL, "
        "correlation_id TEXT NOT NULL, occurred_at TEXT NOT NULL, "
        "authorization_source_kind TEXT NOT NULL DEFAULT 'LEGACY', "
        "authorization_fingerprint TEXT NOT NULL DEFAULT 'legacy-unavailable', "
        "authorization_key_id TEXT, effective_assignment_ids TEXT NOT NULL DEFAULT '[]', "
        "effective_roles TEXT NOT NULL DEFAULT '[]', denied_roles TEXT NOT NULL DEFAULT '[]')"
    )
    _ensure_column(
        conn,
        "v2_authorization_decision_events",
        "authorization_source_kind",
        "TEXT NOT NULL DEFAULT 'LEGACY'",
    )
    _ensure_column(
        conn,
        "v2_authorization_decision_events",
        "authorization_fingerprint",
        "TEXT NOT NULL DEFAULT 'legacy-unavailable'",
    )
    _ensure_column(
        conn,
        "v2_authorization_decision_events",
        "authorization_key_id",
        "TEXT",
    )
    _ensure_column(
        conn,
        "v2_authorization_decision_events",
        "effective_assignment_ids",
        "TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        conn,
        "v2_authorization_decision_events",
        "effective_roles",
        "TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        conn,
        "v2_authorization_decision_events",
        "denied_roles",
        "TEXT NOT NULL DEFAULT '[]'",
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_diagnostic_events("
        "diagnostic_event_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL, "
        "code TEXT NOT NULL, category TEXT NOT NULL, user_safe_cause TEXT NOT NULL, "
        "user_safe_impact TEXT NOT NULL, permitted_remedies_json TEXT NOT NULL, "
        "retryability TEXT NOT NULL, mutation_outcome TEXT NOT NULL, actor_id TEXT, "
        "component TEXT NOT NULL, occurred_at TEXT NOT NULL, taxonomy_version TEXT NOT NULL, "
        "metadata_json TEXT NOT NULL DEFAULT '{}')"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_diagnostics_correlation "
        "ON v2_diagnostic_events(correlation_id,occurred_at)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_audit_streams("
        "stream_id TEXT PRIMARY KEY, stream_type TEXT NOT NULL "
        "CHECK(stream_type IN ('GLOBAL','RULE_GOVERNANCE','REVIEW','SECURITY','DISPOSAL')), "
        "review_id TEXT, genesis_hmac TEXT NOT NULL, current_sequence INTEGER NOT NULL CHECK(current_sequence>=0), "
        "current_hmac TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=0), "
        "UNIQUE(stream_type, review_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_audit_events("
        "event_id TEXT PRIMARY KEY, stream_id TEXT NOT NULL REFERENCES v2_audit_streams(stream_id), "
        "stream_sequence INTEGER NOT NULL CHECK(stream_sequence>0), schema_version INTEGER NOT NULL, "
        "actor_id TEXT NOT NULL, actor_display TEXT NOT NULL, identity_source TEXT NOT NULL, "
        "occurred_at TEXT NOT NULL, event_type TEXT NOT NULL, canonical_payload TEXT NOT NULL, "
        "correlation_id TEXT NOT NULL, outcome TEXT NOT NULL, prior_hmac TEXT NOT NULL, "
        "event_hmac TEXT NOT NULL, UNIQUE(stream_id, stream_sequence))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_audit_event_scopes("
        "event_id TEXT NOT NULL REFERENCES v2_audit_events(event_id), ordinal INTEGER NOT NULL, "
        "resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, PRIMARY KEY(event_id, ordinal))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_generation_analytical_state_events("
        "event_id TEXT PRIMARY KEY, generation_id TEXT NOT NULL, review_id TEXT NOT NULL "
        "REFERENCES v2_review_cycles(review_id), ordinal INTEGER NOT NULL CHECK(ordinal>0), "
        "origin TEXT NOT NULL CHECK(origin IN ('NATIVE','LEGACY_SNAPSHOT')), prior_state TEXT, "
        "new_state TEXT NOT NULL CHECK(new_state IN ('VERIFIED','ANALYZED','SUMMARIZED','EXPORTED')), "
        "trigger_type TEXT NOT NULL, trigger_id TEXT, actor_id TEXT, occurred_at TEXT, event_hash TEXT NOT NULL, "
        "UNIQUE(generation_id, ordinal), UNIQUE(generation_id, new_state))"
    )
    for table in _APPEND_ONLY_TABLES:
        _append_only_triggers(conn, table)
    _backfill_legacy_cycles(conn)


def _month_number(month: str) -> int:
    normalized = (month or "").strip().lower()
    for number in range(1, 13):
        if normalized in (calendar.month_name[number].lower(), calendar.month_abbr[number].lower()):
            return number
    return 1


def _legacy_candidate_id(review_id: str) -> str:
    return "cand_legacy_" + hashlib.sha256(review_id.encode("utf-8")).hexdigest()[:24]


def _legacy_event_id(kind: str, review_id: str) -> str:
    return "evt_legacy_" + hashlib.sha256((kind + "\0" + review_id).encode()).hexdigest()[:24]


def _legacy_generation(conn, review_id: str):
    row = conn.execute(
        "SELECT generation_id FROM review_generations WHERE cycle_id=? "
        "ORDER BY sequence_number DESC LIMIT 1",
        (review_id,),
    ).fetchone()
    return row[0] if row else None


def _backfill_legacy_cycles(conn) -> None:
    """Adopt legacy review identities without pretending they were native opaque IDs or native events."""

    rows = conn.execute("SELECT cycle_id, month, year, state FROM cycles ORDER BY cycle_id").fetchall()
    for review_id, month, year_text, state in rows:
        exists = conn.execute(
            "SELECT 1 FROM v2_review_cycles WHERE review_id=?", (review_id,)
        ).fetchone()
        if exists:
            continue
        audit = conn.execute(
            "SELECT actor, ts FROM audit WHERE cycle_id=? ORDER BY seq LIMIT 1", (review_id,)
        ).fetchone()
        actor, occurred = audit if audit else ("legacy-system", "1970-01-01T00:00:00Z")
        actor = actor or "legacy-system"
        occurred = occurred or "1970-01-01T00:00:00Z"
        try:
            year = int(year_text)
        except (TypeError, ValueError):
            year = 1000
        year = max(1000, min(9999, year))
        month_number = _month_number(month)
        conn.execute(
            "INSERT INTO v2_review_cycles(review_id,selected_month,selected_year,creation_actor_id,"
            "creation_actor_display,identity_source,created_at,origin) VALUES(?,?,?,?,?,?,?,?)",
            (
                review_id,
                month_number,
                year,
                actor,
                actor,
                "LEGACY",
                occurred,
                "LEGACY_SNAPSHOT",
            ),
        )
        generation_id = _legacy_generation(conn, review_id)
        if state in ("Created", "Intake", "Processed"):
            candidate_id = _legacy_candidate_id(review_id)
            conn.execute(
                "INSERT INTO v2_working_candidates(candidate_id,review_id,predecessor_generation_id,"
                "creation_trigger,extractor_profile_id,creator_actor_id,created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    candidate_id,
                    review_id,
                    None,
                    "LEGACY_ADOPTION",
                    "LEGACY",
                    actor,
                    occurred,
                ),
            )
            status = "Draft" if state == "Created" else "Data Uploaded"
            owner_kind, owner_id = "WorkingCandidate", candidate_id
            working_generation = published_generation = None
        else:
            status = "Data Reviewed" if state == "Verified" else "Validation Complete"
            owner_kind = "ReviewGeneration"
            owner_id = generation_id or ("gen_legacy_" + hashlib.sha256(review_id.encode()).hexdigest()[:24])
            candidate_id = None
            working_generation = generation_id
            published_generation = generation_id if state in ("Analyzed", "Summarized", "Exported") else None
        conn.execute(
            "INSERT INTO v2_review_cycle_pointers(review_id,active_candidate_id,working_generation_id,"
            "published_generation_id,current_rule_set_id,revision) VALUES(?,?,?,?,?,?)",
            (review_id, candidate_id, working_generation, published_generation, None, 0),
        )
        conn.execute(
            "INSERT INTO v2_review_disposition_events(event_id,review_id,sequence,disposition,actor_id,"
            "occurred_at,reason) VALUES(?,?,?,?,?,?,?)",
            (
                _legacy_event_id("disposition", review_id),
                review_id,
                1,
                "Active",
                actor,
                occurred,
                "LEGACY_SNAPSHOT",
            ),
        )
        conn.execute(
            "INSERT INTO v2_review_status_events(event_id,review_id,owner_kind,owner_id,sequence,"
            "previous_status,status,actor_id,occurred_at,reason,origin) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                _legacy_event_id("status", review_id),
                review_id,
                owner_kind,
                owner_id,
                1,
                None,
                status,
                actor,
                occurred,
                "LEGACY_SNAPSHOT",
                "LEGACY_SNAPSHOT",
            ),
        )
