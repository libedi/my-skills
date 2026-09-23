import copy
import unittest

import validate


def state():
    return {
        "research_id": "R-1", "original_request": "Why did latency increase?",
        "plan_version": 1,
        "units": [{
            "id": "U1", "subproblem_id": "S1",
            "required_questions": [{"id": "Q1", "importance": "critical",
                                    "sufficient_when": "Direct measurements and alternatives checked"}],
            "axes": [{"id": "A", "question": "Did database time increase?",
                      "required_question_ids": ["Q1"]}],
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
        "units": {"U1": {"entries": [
            {"id": "W1", "round": 1, "kind": "explore", "target": "A",
             "state": "finished", "dispatched_at": "2026-09-23T00:00:00Z"}]}},
        "request_usage": {"consistency_work_items": 0},
    }


def result():
    return {
        "research_id": "R-1", "unit_id": "U1", "axis_id": "A", "plan_version": 1,
        "status": "complete", "answer_summary": "Database time increased.",
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
    def check(self, fn, *args):
        c = validate.Check()
        fn(*args, c)
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
        entries = l["units"]["U1"]["entries"]
        entries.extend([
            {"id": "W2", "round": 1, "kind": "explore", "target": "B",
             "state": "failed", "dispatched_at": "2026-09-23T00:01:00Z"},
            {"id": "W3", "round": 1, "kind": "explore", "target": "C",
             "state": "cancelled", "dispatched_at": "2026-09-23T00:02:00Z"},
            {"id": "W4", "round": 1, "kind": "explore", "target": "D",
             "state": "reserved"},
        ])
        self.assertTrue(any("initial" in x for x in self.check(validate.dispatch, l).errors))
        entries[-1] = {"id": "W4", "round": 1, "kind": "explore", "target": "D",
                       "state": "cancelled", "dispatched_at": None,
                       "release_reason": "Plan changed before dispatch"}
        self.assertFalse(self.check(validate.dispatch, l).errors)

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


if __name__ == "__main__":
    unittest.main()
