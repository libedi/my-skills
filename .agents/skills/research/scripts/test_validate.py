import copy
import unittest

import validate


def usage(limit=30, used=0):
    return {"limit": limit, "used": used,
            "calls": [{"tool": "web_fetch", "purpose": "Check primary evidence"} for _ in range(used)]}


def axis(ident="A", round=1):
    return {"id": ident, "round": round, "question": "Did database time increase?",
            "objective": "Check the database contribution", "required_question_ids": ["Q1"],
            "scope": ["Database latency"], "exclude": [], "intentional_overlap": [],
            "distinct_from": "Inspect database measurements", "evidence_strategy": "Compare measured intervals",
            "expected_output": "Evidence-backed contribution", "contribution": "Database delay could explain latency",
            "independent_start": "Measurements are available without other findings",
            "assignment_rationale": "Focused examination of database evidence"}


def state():
    return {
        "research_id": "R-1", "original_request": "Why did latency increase?",
        "plan_version": 1,
        "units": [{
            "id": "U1", "subproblem_id": "S1",
            "required_questions": [{"id": "Q1", "importance": "critical",
                                    "sufficient_when": "Direct measurements and alternatives checked"}],
            "axes": [axis()],
            "host_check": {"status": "passed", "plan_version": 1},
            "capacity": {"investigation_slots": 4},
            "plan_review": {"required": False, "triggers": [], "status": "not_required",
                            "plan_version": 1, "invocations": [], "findings": []},
            "coverage_plan": [{"question_id": "Q1", "primary_axis": "A"}],
            "question_coverage": [{"question_id": "Q1", "status": "answered",
                                   "claim_ids": ["R-1/U1/A-C1"]}],
            "result_status": "complete",
            "stop_reasons": ["sufficient"], "unknowns": [], "objections": [],
        }],
    }


def ledger():
    return {
        "research_id": "R-1",
        "units": {"U1": {"initial_axis_ids": ["A"], "entries": [
            {"id": "W1", "round": 1, "kind": "explore", "target": "A",
             "state": "finished", "dispatched_at": "2026-09-23T00:00:00Z",
             "tool_usage": usage()}]}},
        "request_usage": {"consistency_work_items": 0},
    }


def result():
    return {
        "research_id": "R-1", "unit_id": "U1", "axis_id": "A", "plan_version": 1,
        "status": "complete", "answer_summary": "Database time increased.",
        "work_item_id": "W1", "task_kind": "explore", "tool_usage": usage(),
        "claims": [{
            "id": "R-1/U1/A-C1", "statement": "Database time increased.",
            "kind": "fact", "question_ids": ["Q1"],
            "supporting_evidence_ids": ["R-1/U1/A-E1"],
            "contradicting_evidence_ids": [], "premise_claim_ids": [],
            "confidence": "medium", "confidence_reason": "A short observation window",
        }],
        "evidence": [{
            "id": "R-1/U1/A-E1", "source_type": "observation",
            "locator": "latency.csv", "location": "rows 1-10",
            "origin_id": "metric:latency", "observation": "P95 rose",
        }],
        "question_coverage": [{"question_id": "Q1", "status": "answered",
                               "claim_ids": ["R-1/U1/A-C1"]}],
    }


class ValidatorTests(unittest.TestCase):
    def check(self, fn, *args, **kwargs):
        c = validate.Check()
        if fn == validate.dispatch:
            kwargs.setdefault("state", state())
        fn(*args, c, **kwargs)
        return c

    def test_valid_single_unit_contract(self):
        self.assertFalse(self.check(validate.plan, state()).errors)
        self.assertFalse(self.check(validate.dispatch, ledger()).errors)
        self.assertFalse(self.check(validate.result, state(), result()).errors)
        self.assertFalse(self.check(validate.report, state(), ledger()).errors)

    def test_plan_rejects_unmapped_critical_question(self):
        s = state()
        s["units"][0]["coverage_plan"] = []
        c = self.check(validate.plan, s)
        self.assertTrue(any("mapping mismatch" in x for x in c.errors))

    def test_budget_counts_dispatched_failure_but_releases_pre_dispatch_cancel(self):
        l = ledger()
        l["units"]["U1"]["initial_axis_ids"] = ["A", "B", "C"]
        s = state()
        s["units"][0]["axes"] = [axis(i) for i in ["A", "B", "C"]]
        entries = l["units"]["U1"]["entries"]
        entries.extend([
            {"id": "W2", "round": 1, "kind": "explore", "target": "B",
             "state": "failed", "dispatched_at": "2026-09-23T00:01:00Z", "tool_usage": usage()},
            {"id": "W3", "round": 1, "kind": "explore", "target": "C",
             "state": "cancelled", "dispatched_at": "2026-09-23T00:02:00Z", "tool_usage": usage()},
            {"id": "W4", "round": 1, "kind": "explore", "target": "D",
             "state": "reserved", "tool_usage": usage()},
        ])
        self.assertTrue(any("initial" in x for x in self.check(validate.dispatch, l, state=s).errors))
        entries[-1] = {"id": "W4", "round": 1, "kind": "explore", "target": "D",
                       "state": "cancelled", "dispatched_at": None,
                       "release_reason": "Plan changed before dispatch", "tool_usage": usage()}
        self.assertFalse(self.check(validate.dispatch, l, state=s).errors)

    def test_four_initial_axes_and_six_investigation_tasks_are_valid(self):
        s, l = state(), ledger()
        ids = ["A", "B", "C", "D"]
        s["units"][0]["axes"] = [axis(i) for i in ids]
        l["units"]["U1"]["initial_axis_ids"] = ids
        entries = l["units"]["U1"]["entries"]
        entries.extend({"id": f"W{i}", "round": 1, "kind": "explore", "target": ident,
                        "state": "finished", "dispatched_at": "2026-09-26T00:00:00Z",
                        "tool_usage": usage(30, 30)} for i, ident in enumerate(ids[1:], 2))
        entries.extend({"id": f"W{i}", "round": 2, "kind": "verify", "target": "A",
                        "state": "finished", "dispatched_at": "2026-09-26T00:01:00Z",
                        "tool_usage": usage(10, 10)} for i in [5, 6])
        self.assertFalse(self.check(validate.plan, s).errors)
        self.assertFalse(self.check(validate.dispatch, l, state=s).errors)
        self.assertFalse(self.check(validate.report, s, l).errors)
        entries.append({"id": "W7", "round": 2, "kind": "verify", "target": "A",
                        "state": "reserved", "tool_usage": usage(10)})
        self.assertTrue(any("supplementary" in e for e in self.check(validate.dispatch, l, state=s).errors))

    def test_axis_rationales_are_required_but_not_semantically_scored(self):
        s = state()
        del s["units"][0]["axes"][0]["contribution"]
        self.assertTrue(any("contribution" in e for e in self.check(validate.plan, s).errors))
        c = self.check(validate.plan, state())
        self.assertTrue(any("axis quality" in w for w in c.warnings))

    def test_pending_or_stale_release_blocks_dispatch(self):
        for check in [{"status": "pending", "plan_version": 1}, {"status": "passed", "plan_version": 0}]:
            s = state()
            s["units"][0]["host_check"] = check
            self.assertTrue(any("released" in e for e in self.check(validate.dispatch, ledger(), state=s).errors))

    def test_whole_cohort_capacity_blocks_partial_launch(self):
        s, l = state(), ledger()
        s["units"][0]["axes"].append(axis("B"))
        s["units"][0]["capacity"]["investigation_slots"] = 1
        l["units"]["U1"]["initial_axis_ids"].append("B")
        self.assertTrue(any("whole initial cohort" in e for e in self.check(validate.dispatch, l, state=s).errors))

    def test_triggered_review_cannot_be_skipped_or_left_unresolved(self):
        s = state()
        review = s["units"][0]["plan_review"]
        review.update(required=True, triggers=["unclear_overlap"], status="pending")
        self.assertTrue(any("required review" in e for e in self.check(validate.dispatch, ledger(), state=s).errors))
        review.update(status="resolved", invocations=[{"agent_id": "review-1", "tool_usage": usage(10)}])
        review["findings"] = [{"id": "P1", "severity": "major", "resolution": "unresolved"}]
        self.assertTrue(any("substantive finding" in e for e in self.check(validate.dispatch, ledger(), state=s).errors))
        review["findings"][0].update(resolution="rejected_with_evidence", resolution_reason="Separate primary datasets")
        self.assertFalse(self.check(validate.dispatch, ledger(), state=s).errors)
        review["plan_version"] = 0
        self.assertTrue(any("current plan" in e for e in self.check(validate.dispatch, ledger(), state=s).errors))

    def test_plan_review_recheck_limit_and_same_agent(self):
        s = state()
        review = s["units"][0]["plan_review"]
        review.update(required=True, triggers=["forced_partition"], status="resolved",
                      invocations=[{"agent_id": "review-1", "tool_usage": usage(10)} for _ in range(2)])
        self.assertFalse(self.check(validate.plan, s).errors)
        review["invocations"][1]["agent_id"] = "review-2"
        self.assertTrue(any("reuse" in e for e in self.check(validate.plan, s).errors))
        review["invocations"][1]["agent_id"] = "review-1"
        review["invocations"].append(copy.deepcopy(review["invocations"][0]))
        self.assertTrue(any("two review" in e for e in self.check(validate.plan, s).errors))

    def test_tool_call_budget_and_log_mismatch(self):
        l = ledger()
        entry = l["units"]["U1"]["entries"][0]
        entry["tool_usage"] = usage(30, 31)
        self.assertTrue(any("budget exceeded" in e for e in self.check(validate.dispatch, l).errors))
        entry["tool_usage"] = usage(30, 1)
        entry["tool_usage"]["calls"] = []
        self.assertTrue(any("call log" in e for e in self.check(validate.dispatch, l).errors))
        entry["tool_usage"] = usage(31)
        self.assertTrue(any("ceiling" in e for e in self.check(validate.dispatch, l).errors))

    def test_followup_has_ten_calls_without_resetting_initial_usage(self):
        l = ledger()
        entries = l["units"]["U1"]["entries"]
        entries[0]["tool_usage"] = usage(30, 30)
        entries.append({"id": "V1", "round": 2, "kind": "verify", "target": "A",
                        "state": "reserved", "tool_usage": usage(10, 10)})
        self.assertFalse(self.check(validate.dispatch, l).errors)
        self.assertEqual(entries[0]["tool_usage"]["used"], 30)
        entries[1]["tool_usage"] = usage(30)
        self.assertTrue(any("10-call" in e for e in self.check(validate.dispatch, l).errors))

    def test_duplicate_initial_task_cannot_reset_budget(self):
        l = ledger()
        duplicate = copy.deepcopy(l["units"]["U1"]["entries"][0])
        duplicate.update(id="W2", state="reserved")
        l["units"]["U1"]["entries"].append(duplicate)
        self.assertTrue(any("already dispatched" in e for e in self.check(validate.dispatch, l).errors))

    def test_supplement_cannot_start_while_initial_work_is_active(self):
        l = ledger()
        entries = l["units"]["U1"]["entries"]
        entries[0]["state"] = "dispatched"
        entries.append({"id": "V1", "round": 2, "kind": "verify", "target": "A",
                        "state": "reserved", "tool_usage": usage(10)})
        self.assertTrue(any("before the whole" in e for e in self.check(validate.dispatch, l).errors))

    def test_sequential_unit_rule(self):
        s, l = state(), ledger()
        second = copy.deepcopy(s["units"][0])
        second.update(id="U2", subproblem_id="S2")
        s["units"].append(second)
        l["units"]["U2"] = copy.deepcopy(l["units"]["U1"])
        for u in l["units"].values():
            u["entries"][0]["state"] = "dispatched"
        self.assertTrue(any("multiple Units" in e for e in self.check(validate.dispatch, l, state=s).errors))

    def test_complete_requires_cohort_terminal_and_partial_can_report_limits(self):
        s, l = state(), ledger()
        l["units"]["U1"]["entries"][0]["state"] = "dispatched"
        self.assertTrue(any("unfinished work" in e for e in self.check(validate.report, s, l).errors))
        s["units"][0].update(result_status="partial", stop_reasons=["budget_exhausted"],
                             unknowns=[{"state": "unresolved", "question_ids": ["Q1"]}])
        s["units"][0]["host_check"]["status"] = "pending"
        l["units"]["U1"]["entries"][0]["state"] = "failed"
        self.assertFalse(self.check(validate.report, s, l).errors)

    def test_exhausted_result_cannot_hide_unanswered_question(self):
        r = result()
        r["tool_usage"] = usage(30, 30)
        r["question_coverage"][0]["status"] = "partial"
        self.assertTrue(any("unanswered assigned" in e for e in self.check(validate.result, state(), r).errors))
        r["status"] = "partial"
        self.assertFalse(self.check(validate.result, state(), r).errors)

    def test_extra_explorer_requires_recorded_new_axis(self):
        s, l = state(), ledger()
        l["units"]["U1"]["entries"].append({"id": "X1", "round": 2, "kind": "extra_explore",
                                              "target": "B", "state": "reserved", "tool_usage": usage(10)})
        self.assertTrue(any("new round-2 axis" in e for e in self.check(validate.dispatch, l, state=s).errors))
        s["units"][0]["axes"].append(axis("B", 2))
        self.assertFalse(self.check(validate.dispatch, l, state=s).errors)

    def test_consistency_usage_is_recorded(self):
        l = ledger()
        s = state()
        s["subproblems"] = []  # Dispatch only: explicitly recorded complex-request mode.
        l["request_usage"]["consistency_work_items"] = 1
        self.assertTrue(any("count differs" in e for e in self.check(validate.dispatch, l).errors))
        l["request_usage"]["consistency_entries"] = [{"id": "G1", "state": "finished", "tool_usage": usage(10, 10)}]
        self.assertFalse(self.check(validate.dispatch, l, state=s).errors)
        self.assertTrue(any("complex requests only" in e for e in self.check(validate.dispatch, l).errors))

    def test_result_usage_must_match_ledger_work_item(self):
        r, l = result(), ledger()
        self.assertFalse(self.check(validate.result, state(), r, ledger=l).errors)
        r["tool_usage"] = usage(30, 1)
        self.assertTrue(any("differs from ledger usage" in e for e in self.check(validate.result, state(), r, ledger=l).errors))
        r["tool_usage"] = usage()
        r["work_item_id"] = "W9"
        self.assertTrue(any("unknown or duplicate" in e for e in self.check(validate.result, state(), r, ledger=l).errors))

    def test_other_unit_plan_revision_does_not_invalidate_unchanged_unit(self):
        s = state()
        s["plan_version"] = 2
        s["units"][0]["plan_version"] = 1
        self.assertFalse(self.check(validate.result, s, result()).errors)
        self.assertFalse(self.check(validate.report, s, ledger()).errors)

    def test_final_consistency_cannot_overlap_unit_work(self):
        l = ledger()
        l["units"]["U1"]["entries"][0]["state"] = "dispatched"
        l["request_usage"].update(consistency_work_items=1,
                                  consistency_entries=[{"id": "G1", "state": "reserved", "tool_usage": usage(10)}])
        self.assertTrue(any("overlaps" in e for e in self.check(validate.dispatch, l).errors))

    def test_global_partial_can_include_unexecuted_unit(self):
        s, l = state(), ledger()
        second = copy.deepcopy(s["units"][0])
        second.update(id="U2", subproblem_id="S2", result_status=None, question_coverage=[])
        second["host_check"]["status"] = "pending"
        s["units"].append(second)
        l["units"]["U2"] = {"initial_axis_ids": ["A"], "entries": []}
        s.update(parent_questions=[{"id": "PQ1", "importance": "critical"},
                                   {"id": "PQ2", "importance": "critical"}],
                 required_outcomes=["OUT1", "OUT2"],
                 subproblems=[{"id": "S1", "unit_id": "U1", "parent_question_ids": ["PQ1"],
                               "required_outcome_ids": ["OUT1"], "execution_status": "finished", "validity": "current"},
                              {"id": "S2", "unit_id": "U2", "parent_question_ids": ["PQ2"],
                               "required_outcome_ids": ["OUT2"], "execution_status": "blocked", "validity": "current"}],
                 global_coverage=[{"question_id": "PQ1", "primary_subproblem_id": "S1",
                                   "outcome_ids": ["OUT1"], "status": "answered", "report_location": "Answer"},
                                  {"question_id": "PQ2", "primary_subproblem_id": "S2",
                                   "outcome_ids": ["OUT2"], "status": "unanswered"}],
                 global_result={"status": "partial", "stop_reasons": ["access_limited"],
                                "unknowns": [{"state": "inaccessible", "question_ids": ["PQ2"]}], "objections": []})
        self.assertFalse(self.check(validate.report, s, l).errors)
        s["global_result"]["status"] = "complete"
        self.assertTrue(any("unfinished" in e for e in self.check(validate.report, s, l).errors))

    def test_result_rejects_unbacked_fact_and_broken_reference(self):
        r = result()
        r["claims"][0]["supporting_evidence_ids"] = ["R-1/U1/A-E2"]
        c = self.check(validate.result, state(), r)
        self.assertTrue(any("unknown evidence" in x for x in c.errors))

    def test_complete_rejected_with_critical_gap_or_blocking_objection(self):
        s = state()
        s["units"][0]["question_coverage"][0]["status"] = "partial"
        s["units"][0]["objections"] = [{"id": "O1", "severity": "blocking",
                                          "resolution": "unresolved"}]
        c = self.check(validate.report, s, ledger())
        self.assertTrue(any("unanswered critical" in x for x in c.errors))
        self.assertTrue(any("blocking objection" in x for x in c.errors))

    def test_complex_global_complete_rejected_for_stale_outcome(self):
        s = state()
        s["parent_questions"] = [{"id": "PQ1", "importance": "critical"}]
        s["required_outcomes"] = ["OUT1"]
        s["subproblems"] = [{"id": "S1", "unit_id": "U1",
                             "parent_question_ids": ["PQ1"],
                             "required_outcome_ids": ["OUT1"],
                             "execution_status": "finished", "validity": "stale"}]
        s["global_coverage"] = [{"question_id": "PQ1",
                                 "primary_subproblem_id": "S1",
                                 "outcome_ids": ["OUT1"], "status": "answered",
                                 "report_location": "Answer"}]
        s["global_result"] = {"status": "complete", "stop_reasons": ["sufficient"],
                              "unknowns": [], "objections": []}
        c = self.check(validate.report, s, ledger())
        self.assertTrue(any("stale or unfinished" in x for x in c.errors))

    def test_global_complete_waits_for_final_consistency(self):
        s, l = state(), ledger()
        s.update(parent_questions=[{"id": "PQ1", "importance": "critical"}], required_outcomes=["OUT1"],
                 subproblems=[{"id": "S1", "unit_id": "U1", "parent_question_ids": ["PQ1"],
                               "required_outcome_ids": ["OUT1"], "execution_status": "finished", "validity": "current"}],
                 global_coverage=[{"question_id": "PQ1", "primary_subproblem_id": "S1", "outcome_ids": ["OUT1"],
                                   "status": "answered", "report_location": "Answer"}],
                 global_result={"status": "complete", "stop_reasons": ["sufficient"], "unknowns": [], "objections": []})
        l["request_usage"].update(consistency_work_items=1,
                                  consistency_entries=[{"id": "G1", "state": "dispatched", "tool_usage": usage(10)}])
        self.assertTrue(any("unfinished final consistency" in e for e in self.check(validate.report, s, l).errors))
        l["request_usage"]["consistency_entries"][0]["state"] = "finished"
        self.assertFalse(self.check(validate.report, s, l).errors)


if __name__ == "__main__":
    unittest.main()
