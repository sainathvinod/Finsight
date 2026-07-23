# PromptBuilder — pure, deterministic, provider-independent assembly of a PromptRequest from
# deterministic grounding, conversation history, and human-controlled review memory. Given identical
# inputs it returns a byte-identical PromptRequest. It does NOT mask, call a provider, log, mutate its
# inputs, or perform any I/O. Finding order uses the domain's authoritative Severity ranks (not an
# invented ordering); all other sections use stable total-order sort keys.
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence

from finsight.application.ai.contracts import PromptRequest
from finsight.application.ai.prompt.budget import ContextBudget, TruncationReport
from finsight.application.ai.prompt.schema import OUTPUT_SCHEMA_VERSION, output_schema
from finsight.application.ai.prompt.system_prompt import SYSTEM_PROMPT_VERSION, system_prompt
from finsight.domain.ai.contracts import (
    AiGroundingContext, ConversationMessage, MemoryType, ReviewMemoryEntry,
)
from finsight.domain.findings import Severity

_SEVERITY_RANK = {s.label: s.rank for s in Severity}


@dataclass(frozen=True)
class PromptBuildResult:
    request: PromptRequest
    truncation: TruncationReport


def _sev_rank(label: str) -> int:
    return _SEVERITY_RANK.get(label, 0)     # unknown label sorts last, deterministically


def _keep_tail(items, limit):
    """Keep the most-recent `limit` items (input already in ascending/chronological order)."""
    if limit is None or len(items) <= limit:
        return list(items), 0
    return list(items[len(items) - limit:]), len(items) - limit


def _keep_head(items, limit):
    if limit is None or len(items) <= limit:
        return list(items), 0
    return list(items[:limit]), len(items) - limit


class PromptBuilder:
    """Pure, deterministic, provider-independent PromptRequest assembler."""

    def __init__(self, budget: ContextBudget,
                 system_prompt_version: str = SYSTEM_PROMPT_VERSION,
                 schema_version: str = OUTPUT_SCHEMA_VERSION):
        self._budget = budget
        self._sys_ver = system_prompt_version
        self._schema_ver = schema_version

    def build(self, *, grounding: AiGroundingContext, question: str,
              conversation: Sequence[ConversationMessage] = (),
              memory: Sequence[ReviewMemoryEntry] = (),
              audience: Optional[str] = None,
              answer_detail: Optional[str] = None) -> PromptBuildResult:
        lines: List[str] = []
        f_trim = 0

        r = grounding.review
        if r is not None:
            lines.append("REVIEW %s (%s %s) — state=%s, findings=%d"
                         % (r.cycle_id, r.month, r.year, r.state, r.finding_count))
        else:
            lines.append("REVIEW: (none)")

        s = grounding.summary
        if s is not None:
            lines.append("SUMMARY: status=%s, findings=%d" % (s.status_label, s.finding_count))

        rr = grounding.rule_run
        if rr is not None:
            lines.append("RULE RUN [run:%s]: ruleset=%s, config=%s, fingerprint=%s, findings=%d"
                         % (rr.run_id, rr.ruleset_version, rr.config_version, rr.input_fingerprint,
                            rr.finding_count))

        # review memory (human-controlled), most-recent kept
        mem_sorted = sorted(memory, key=lambda e: (e.created_ts, e.memory_id))
        kept_mem, m_drop = _keep_tail(mem_sorted, self._budget.max_memory_entries)
        lines.append("REVIEW MEMORY:")
        if kept_mem:
            for e in kept_mem:
                line = "- [memory:%s] type=%s: %s" % (e.memory_id, e.memory_type.value, e.content)
                if e.memory_type == MemoryType.SYSTEM_DERIVED and (e.source_type or e.source_id):
                    line += " (source=%s/%s)" % (e.source_type, e.source_id)
                lines.append(line)
        else:
            lines.append("- (none)")

        # findings — severity desc, then account, then id; beyond budget => citation-key-only lines
        f_sorted = sorted(grounding.findings, key=lambda f: (-_sev_rank(f.severity), f.account, f.id))
        limit = self._budget.max_findings
        lines.append("FINDINGS:")
        if f_sorted:
            for i, f in enumerate(f_sorted):
                if limit is not None and i >= limit:
                    lines.append("- [finding:%s] (detail omitted by budget)" % f.id)
                    f_trim += 1
                    continue
                lines.append("- [finding:%s] account=%s rule=%s severity=%s type=%s period=%s state=%s"
                             % (f.id, f.account, f.rule_id, f.severity, f.finding_type, f.period, f.state))
                ev = "; ".join("%s=%s" % (k, v) for k, v in sorted(f.evidence.items()))
                lines.append("    evidence: %s" % (ev if ev else "(none)"))
                lines.append("    sources: %s" % ("; ".join(f.source_refs) if f.source_refs else "(none)"))
        else:
            lines.append("- (none)")

        # provenance — stable order, head kept
        p_sorted = sorted(grounding.provenance, key=lambda p: (p.doc_type, p.name, p.fingerprint))
        kept_p, p_drop = _keep_head(p_sorted, self._budget.max_provenance_items)
        lines.append("PROVENANCE:")
        if kept_p:
            for p in kept_p:
                lines.append("- [prov:%s] doc_type=%s name=%s period=%s"
                             % (p.fingerprint, p.doc_type, p.name, p.period))
        else:
            lines.append("- (none)")

        # audit — ordered by ts/action/actor, most-recent kept
        a_sorted = sorted(grounding.audit_events, key=lambda e: (e.ts, e.action, e.actor))
        kept_a, a_drop = _keep_tail(a_sorted, self._budget.max_audit_events)
        lines.append("AUDIT:")
        if kept_a:
            for e in kept_a:
                lines.append("- [audit:%s@%s] actor=%s" % (e.action, e.ts, e.actor))
        else:
            lines.append("- (none)")

        context_block = "\n".join(lines)

        # conversation — chronological (seq), most-recent kept, rendered chronologically
        conv_sorted = sorted(conversation, key=lambda m: (m.seq, m.message_id))
        kept_conv, c_drop = _keep_tail(conv_sorted, self._budget.max_conversation_messages)
        conv_lines = ["CONVERSATION:"]
        if kept_conv:
            for m in kept_conv:
                conv_lines.append("- [%s] %s" % (m.role.value, m.content))
        else:
            conv_lines.append("- (none)")
        conversation_block = "\n".join(conv_lines)

        report = TruncationReport(findings_trimmed=f_trim, conversation_dropped=c_drop,
                                  memory_dropped=m_drop, provenance_dropped=p_drop, audit_dropped=a_drop)
        request = PromptRequest(
            system_prompt=self._render_system(audience, answer_detail),
            context_block=context_block,
            conversation_block=conversation_block,
            question=question,
            output_schema=output_schema(self._schema_ver),
            prompt_version=self._sys_ver,           # prompt version tracks the system-prompt version
            schema_version=self._schema_ver,
        )
        return PromptBuildResult(request, report)

    def _render_system(self, audience: Optional[str], answer_detail: Optional[str]) -> str:
        text = system_prompt(self._sys_ver)
        directives = []
        if audience:
            directives.append("Audience: %s." % audience)
        if answer_detail:
            directives.append("Answer detail: %s." % answer_detail)
        if directives:
            text = text + "\n\n" + " ".join(directives)
        return text
