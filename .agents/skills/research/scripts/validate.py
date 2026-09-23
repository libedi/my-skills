#!/usr/bin/env python3
"""Deterministic structural checks for the research skill; not evidence verification."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_LIMITS = {
    "initial": 3, "rounds": 2, "supplementary": 2,
    "extra_explorer": 1, "critic": 1, "retry": 1,
    "investigation_total": 5, "status_check": 1,
}
INITIAL = {"explore"}
SUPPLEMENT = {"extra_explore", "verify", "critic", "retry"}
KINDS = INITIAL | SUPPLEMENT | {"status_check"}
STATES = {"reserved", "dispatched", "finished", "failed", "cancelled"}
COVERAGE = {"answered", "partial", "unanswered"}
RESULT_STATES = {"complete", "partial", "needs_user_decision"}
STOP_REASONS = {
    "sufficient", "budget_exhausted", "access_limited", "execution_failed",
    "unresolved_objection", "low_expected_gain", "user_cancelled", "user_input_required",
}


class Check:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")

    def object(self, value, path: str) -> dict:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return {}
        return value

    def array(self, value, path: str) -> list:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        return value

    def nonempty(self, value, path: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a nonempty string")
            return False
        return True

    def ids(self, items: list, path: str) -> set[str]:
        found: set[str] = set()
        for i, item in enumerate(items):
            obj = self.object(item, f"{path}[{i}]")
            ident = obj.get("id")
            if self.nonempty(ident, f"{path}[{i}].id"):
                if ident in found:
                    self.error(path, f"duplicate ID {ident}")
                found.add(ident)
        return found

    def output(self, stage: str) -> dict:
        return {"stage": stage, "ok": not self.errors, "errors": self.errors, "warnings": self.warnings}


def plan(state: dict, c: Check) -> None:
    root = c.object(state, "state")
    c.nonempty(root.get("research_id"), "research_id")
    c.nonempty(root.get("original_request"), "original_request")
    version = root.get("plan_version")
    if type(version) is not int or version < 1:
        c.error("plan_version", "must be a positive integer")
    units = c.array(root.get("units"), "units")
    if not units:
        c.error("units", "at least one Research Unit is required")
    unit_ids = c.ids(units, "units")
    for ui, raw in enumerate(units):
        unit = c.object(raw, f"units[{ui}]")
        p = f"units[{ui}]"
        questions = c.array(unit.get("required_questions"), f"{p}.required_questions")
        qids = c.ids(questions, f"{p}.required_questions")
        if not questions:
            c.error(f"{p}.required_questions", "at least one question is required")
        if not any(isinstance(q, dict) and q.get("importance") == "critical" for q in questions):
            c.error(f"{p}.required_questions", "at least one critical question is required")
        for qi, q in enumerate(questions):
            q = c.object(q, f"{p}.required_questions[{qi}]")
            if q.get("importance") not in {"critical", "supporting"}:
                c.error(f"{p}.required_questions[{qi}].importance", "invalid importance")
            c.nonempty(q.get("sufficient_when"), f"{p}.required_questions[{qi}].sufficient_when")
        axes = c.array(unit.get("axes"), f"{p}.axes")
        if not 1 <= len(axes) <= 3:
            c.error(f"{p}.axes", "must contain 1 to 3 initial axes")
        aids = c.ids(axes, f"{p}.axes")
        for ai, axis in enumerate(axes):
            axis = c.object(axis, f"{p}.axes[{ai}]")
            c.nonempty(axis.get("question"), f"{p}.axes[{ai}].question")
            assigned = c.array(axis.get("required_question_ids"), f"{p}.axes[{ai}].required_question_ids")
            for qid in assigned:
                if qid not in qids:
                    c.error(f"{p}.axes[{ai}]", f"unknown question ID {qid}")
        coverage = c.array(unit.get("coverage_plan"), f"{p}.coverage_plan")
        seen: set[str] = set()
        for ci, raw_cov in enumerate(coverage):
            cov = c.object(raw_cov, f"{p}.coverage_plan[{ci}]")
            qid, aid = cov.get("question_id"), cov.get("primary_axis")
            if qid in seen:
                c.error(f"{p}.coverage_plan", f"duplicate question ID {qid}")
            seen.add(qid)
            if qid not in qids or aid not in aids:
                c.error(f"{p}.coverage_plan[{ci}]", "unknown question or primary axis")
            elif not any(isinstance(a, dict) and a.get("id") == aid
                         and qid in a.get("required_question_ids", []) for a in axes):
                c.error(f"{p}.coverage_plan[{ci}]", "primary axis does not own question")
        if seen != qids:
            c.error(f"{p}.coverage_plan", f"question mapping mismatch: missing={sorted(qids-seen)}, extra={sorted(seen-qids)}")

    subproblems = root.get("subproblems")
    if subproblems is None:
        return
    sps = c.array(subproblems, "subproblems")
    spids = c.ids(sps, "subproblems")
    parent = c.array(root.get("parent_questions"), "parent_questions")
    parent_ids = c.ids(parent, "parent_questions")
    outcomes = c.array(root.get("required_outcomes"), "required_outcomes")
    outcomes_set = {x for x in outcomes if isinstance(x, str)}
    mapped_outcomes: set[str] = set()
    for i, raw in enumerate(sps):
        sp = c.object(raw, f"subproblems[{i}]")
        if sp.get("unit_id") not in unit_ids:
            c.error(f"subproblems[{i}].unit_id", "unknown Unit")
        for qid in c.array(sp.get("parent_question_ids"), f"subproblems[{i}].parent_question_ids"):
            if qid not in parent_ids:
                c.error(f"subproblems[{i}]", f"unknown parent question {qid}")
        for oid in c.array(sp.get("required_outcome_ids"), f"subproblems[{i}].required_outcome_ids"):
            mapped_outcomes.add(oid)
            if oid not in outcomes_set:
                c.error(f"subproblems[{i}]", f"unknown outcome {oid}")
    if mapped_outcomes != outcomes_set:
        c.error("required_outcomes", f"unmapped outcomes {sorted(outcomes_set-mapped_outcomes)}")
    gcov = c.array(root.get("global_coverage"), "global_coverage")
    gcov_ids: set[str] = set()
    for i, raw in enumerate(gcov):
        cov = c.object(raw, f"global_coverage[{i}]")
        qid = cov.get("question_id")
        if qid in gcov_ids:
            c.error("global_coverage", f"duplicate question {qid}")
        gcov_ids.add(qid)
        if qid not in parent_ids or cov.get("primary_subproblem_id") not in spids:
            c.error(f"global_coverage[{i}]", "unknown parent question or Subproblem")
    if gcov_ids != parent_ids:
        c.error("global_coverage", f"parent question mapping mismatch: {sorted(parent_ids-gcov_ids)}")
    edges: dict[str, set[str]] = {sid: set() for sid in spids}
    for i, raw in enumerate(c.array(root.get("dependencies", []), "dependencies")):
        dep = c.object(raw, f"dependencies[{i}]")
        src, dst, kind = dep.get("from"), dep.get("to"), dep.get("type")
        if src not in spids or dst not in spids or kind not in {"factual", "decision", "shared_source"}:
            c.error(f"dependencies[{i}]", "invalid endpoint or type")
        elif kind != "shared_source":
            edges[src].add(dst)
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting:
            c.error("dependencies", f"cycle involving {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt in edges[node]:
            visit(nxt)
        visiting.remove(node)
        visited.add(node)
    for sid in spids:
        visit(sid)


def dispatch(ledger: dict, c: Check, selected_unit: str | None = None) -> None:
    root = c.object(ledger, "ledger")
    c.nonempty(root.get("research_id"), "research_id")
    units = c.object(root.get("units"), "units")
    if selected_unit is not None and selected_unit not in units:
        c.error("unit", f"unknown Unit {selected_unit}")
    for uid, raw in units.items():
        if selected_unit is not None and uid != selected_unit:
            continue
        unit = c.object(raw, f"units.{uid}")
        limits = c.object(unit.get("limits", DEFAULT_LIMITS), f"units.{uid}.limits")
        for key, ceiling in DEFAULT_LIMITS.items():
            value = limits.get(key, ceiling)
            if type(value) is not int or value < 0:
                c.error(f"units.{uid}.limits.{key}", "must be a nonnegative integer")
            elif value > ceiling and not (unit.get("authorized_limit_override") is True
                    and isinstance(unit.get("authorization_reference"), str)
                    and unit["authorization_reference"].strip()):
                c.error(f"units.{uid}.limits.{key}", "exceeds default without authorization reference")
        entries = c.array(unit.get("entries"), f"units.{uid}.entries")
        c.ids(entries, f"units.{uid}.entries")
        counts = {"initial": 0, "supplementary": 0, "extra_explorer": 0,
                  "critic": 0, "retry": 0, "investigation_total": 0, "status_check": 0}
        for i, raw_entry in enumerate(entries):
            e = c.object(raw_entry, f"units.{uid}.entries[{i}]")
            p = f"units.{uid}.entries[{i}]"
            kind, st, rnd = e.get("kind"), e.get("state"), e.get("round")
            if kind not in KINDS or st not in STATES:
                c.error(p, "invalid kind or state")
                continue
            if not c.nonempty(e.get("target"), f"{p}.target"):
                continue
            if st == "cancelled" and e.get("dispatched_at") is None:
                if not c.nonempty(e.get("release_reason"), f"{p}.release_reason"):
                    continue
                continue
            if kind == "explore" and rnd != 1:
                c.error(p, "initial exploration must be Round 1")
            if kind in SUPPLEMENT and rnd != 2:
                c.error(p, "supplementary task must be Round 2")
            if kind != "status_check" and (type(rnd) is not int or rnd < 1 or rnd > limits.get("rounds", 2)):
                c.error(p, "invalid Round")
            if kind == "explore":
                counts["initial"] += 1
            elif kind == "status_check":
                counts["status_check"] += 1
            else:
                counts["supplementary"] += 1
                if kind == "extra_explore":
                    counts["extra_explorer"] += 1
                if kind in {"critic", "retry"}:
                    counts[kind] += 1
            if kind != "status_check":
                counts["investigation_total"] += 1
        for key, count in counts.items():
            limit = limits.get(key, DEFAULT_LIMITS[key])
            if type(limit) is int and count > limit:
                c.error(f"units.{uid}.{key}", f"{count} tasks exceeds limit {limit}")
    usage = c.object(root.get("request_usage", {}), "request_usage")
    consistency = usage.get("consistency_work_items", 0)
    if type(consistency) is not int or not 0 <= consistency <= 2:
        c.error("request_usage.consistency_work_items", "must be an integer from 0 to 2")


def result(state: dict, res: dict, c: Check) -> None:
    root = c.object(state, "state")
    obj = c.object(res, "result")
    rid, uid, aid = obj.get("research_id"), obj.get("unit_id"), obj.get("axis_id")
    if rid != root.get("research_id"):
        c.error("result.research_id", "does not match state")
    units = [u for u in root.get("units", []) if isinstance(u, dict) and u.get("id") == uid]
    if len(units) != 1:
        c.error("result.unit_id", "unknown Unit")
        return
    unit = units[0]
    if aid not in {a.get("id") for a in unit.get("axes", []) if isinstance(a, dict)}:
        c.error("result.axis_id", "unknown axis")
    if obj.get("plan_version") != root.get("plan_version"):
        c.error("result.plan_version", "does not match current plan")
    if obj.get("status") not in {"complete", "partial", "failed"}:
        c.error("result.status", "invalid status")
    c.nonempty(obj.get("answer_summary"), "result.answer_summary")
    questions = {q.get("id") for q in unit.get("required_questions", []) if isinstance(q, dict)}
    evidence = c.array(obj.get("evidence"), "result.evidence")
    claims = c.array(obj.get("claims"), "result.claims")
    eids = c.ids(evidence, "result.evidence")
    cids = c.ids(claims, "result.claims")
    prefix = f"{re.escape(str(rid))}/{re.escape(str(uid))}/{re.escape(str(aid))}"
    for i, raw in enumerate(evidence):
        e = c.object(raw, f"result.evidence[{i}]")
        if not re.fullmatch(prefix + r"-E[1-9][0-9]*", str(e.get("id", ""))):
            c.error(f"result.evidence[{i}].id", "invalid scoped evidence ID")
        for key in ("source_type", "locator", "location", "origin_id", "observation"):
            c.nonempty(e.get(key), f"result.evidence[{i}].{key}")
    for i, raw in enumerate(claims):
        claim = c.object(raw, f"result.claims[{i}]")
        p = f"result.claims[{i}]"
        if not re.fullmatch(prefix + r"-C[1-9][0-9]*", str(claim.get("id", ""))):
            c.error(f"{p}.id", "invalid scoped claim ID")
        c.nonempty(claim.get("statement"), f"{p}.statement")
        if claim.get("kind") not in {"fact", "inference", "proposal"}:
            c.error(f"{p}.kind", "invalid kind")
        if claim.get("confidence") not in {"high", "medium", "low"}:
            c.error(f"{p}.confidence", "invalid confidence")
        c.nonempty(claim.get("confidence_reason"), f"{p}.confidence_reason")
        for qid in c.array(claim.get("question_ids"), f"{p}.question_ids"):
            if qid not in questions:
                c.error(p, f"unknown question {qid}")
        support = c.array(claim.get("supporting_evidence_ids"), f"{p}.supporting_evidence_ids")
        if claim.get("kind") == "fact" and not support:
            c.error(p, "fact has no supporting evidence")
        for field in ("supporting_evidence_ids", "contradicting_evidence_ids"):
            for eid in c.array(claim.get(field), f"{p}.{field}"):
                if eid not in eids:
                    c.error(p, f"unknown evidence {eid}")
        for cid in c.array(claim.get("premise_claim_ids"), f"{p}.premise_claim_ids"):
            if cid not in cids:
                c.error(p, f"unknown premise claim {cid}")
    covered: set[str] = set()
    for i, raw in enumerate(c.array(obj.get("question_coverage"), "result.question_coverage")):
        cov = c.object(raw, f"result.question_coverage[{i}]")
        qid = cov.get("question_id")
        if qid in covered:
            c.error("result.question_coverage", f"duplicate question {qid}")
        covered.add(qid)
        if qid not in questions or cov.get("status") not in COVERAGE:
            c.error(f"result.question_coverage[{i}]", "invalid question or status")
        linked = c.array(cov.get("claim_ids"), f"result.question_coverage[{i}].claim_ids")
        if cov.get("status") == "answered" and not linked:
            c.error(f"result.question_coverage[{i}]", "answered question has no claims")
        for cid in linked:
            if cid not in cids:
                c.error(f"result.question_coverage[{i}]", f"unknown claim {cid}")
    if not covered:
        c.error("result.question_coverage", "at least one coverage entry is required")
    c.warn("result", "evidence relevance, source independence, and decisive summary completeness require human/agent review")


def status_check(obj: dict, questions: list, path: str, c: Check) -> None:
    status = obj.get("result_status", obj.get("status"))
    if status not in RESULT_STATES:
        c.error(f"{path}.status", "invalid final status")
        return
    coverage = {x.get("question_id"): x for x in obj.get("question_coverage", [])
                if isinstance(x, dict)}
    critical = {q.get("id") for q in questions if isinstance(q, dict) and q.get("importance") == "critical"}
    if status == "complete":
        for qid in critical:
            if coverage.get(qid, {}).get("status") != "answered":
                c.error(path, f"complete with unanswered critical question {qid}")
    else:
        reasons = obj.get("stop_reasons")
        if not isinstance(reasons, list) or not reasons or any(r not in STOP_REASONS for r in reasons):
            c.error(f"{path}.stop_reasons", "partial/decision status needs valid reasons")
        unknowns = obj.get("unknowns")
        if not isinstance(unknowns, list) or not any(isinstance(u, dict)
                and u.get("state") in {"unresolved", "inaccessible", "human_decision"}
                and u.get("question_ids") for u in unknowns):
            c.error(f"{path}.unknowns", "partial/decision status needs a linked unresolved Unknown")
        if status == "needs_user_decision" and not any(isinstance(u, dict)
                and u.get("state") == "human_decision" for u in (unknowns or [])):
            c.error(f"{path}.unknowns", "needs_user_decision requires human_decision Unknown")
    for i, raw in enumerate(obj.get("objections", [])):
        ob = c.object(raw, f"{path}.objections[{i}]")
        if ob.get("severity") == "blocking":
            if ob.get("resolution") not in {"accepted", "rejected_with_evidence"}:
                if status == "complete":
                    c.error(path, f"complete with unresolved blocking objection {ob.get('id')}")
            elif not isinstance(ob.get("resolution_reason"), str) or not ob["resolution_reason"].strip():
                c.error(f"{path}.objections[{i}]", "resolved blocking objection lacks reason")
            elif ob.get("resolution") == "accepted":
                c.warn(f"{path}.objections[{i}]", "check that accepted objection changed the conclusion")


def report(state: dict, ledger: dict, c: Check) -> None:
    plan(state, c)
    dispatch(ledger, c)
    if state.get("research_id") != ledger.get("research_id"):
        c.error("research_id", "state and ledger differ")
    for i, raw in enumerate(state.get("units", [])):
        unit = c.object(raw, f"units[{i}]")
        status_check(unit, unit.get("required_questions", []), f"units[{i}]", c)
    sps = state.get("subproblems")
    if sps is None:
        return
    global_result = c.object(state.get("global_result"), "global_result")
    global_result["question_coverage"] = state.get("global_coverage", [])
    status_check(global_result, state.get("parent_questions", []), "global_result", c)
    if global_result.get("status") == "complete":
        outcomes = set(state.get("required_outcomes", []))
        mapped = set()
        for cov in state.get("global_coverage", []):
            if isinstance(cov, dict) and cov.get("status") == "answered" and cov.get("report_location"):
                mapped.update(cov.get("outcome_ids", []))
        if outcomes - mapped:
            c.error("global_result", f"complete with unmapped report outcomes {sorted(outcomes-mapped)}")
        critical = {q.get("id") for q in state.get("parent_questions", [])
                    if isinstance(q, dict) and q.get("importance") == "critical"}
        for i, sp in enumerate(sps):
            if not isinstance(sp, dict):
                continue
            essential = bool(set(sp.get("parent_question_ids", [])) & critical
                             or sp.get("required_outcome_ids"))
            if essential and (sp.get("validity") != "current" or sp.get("execution_status") != "finished"):
                c.error(f"subproblems[{i}]", "essential result is stale or unfinished")


def load(path: str) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="stage", required=True)
    for name in ("plan", "dispatch", "result", "report"):
        cmd = sub.add_parser(name)
        if name in {"plan", "result", "report"}:
            cmd.add_argument("--state", required=True)
        if name in {"dispatch", "report"}:
            cmd.add_argument("--ledger", required=True)
        if name == "dispatch":
            cmd.add_argument("--unit")
        if name == "result":
            cmd.add_argument("--result", required=True)
    args = parser.parse_args(argv)
    c = Check()
    try:
        if args.stage == "plan":
            plan(load(args.state), c)
        elif args.stage == "dispatch":
            dispatch(load(args.ledger), c, args.unit)
        elif args.stage == "result":
            result(load(args.state), load(args.result), c)
        else:
            report(load(args.state), load(args.ledger), c)
    except ValueError as exc:
        c.error("input", str(exc))
    print(json.dumps(c.output(args.stage), ensure_ascii=False, indent=2))
    return 0 if not c.errors else 1


if __name__ == "__main__":
    sys.exit(main())
