# JSON contracts for structural checks

Runtime records are JSON. The integrated design's YAML examples express the same logical fields. This contract changes the former three-initial-axis schema; old run records need explicit migration before reuse, not silent budget reset.

## State and plan release

`state.json` contains `research_id`, `plan_version`, `original_request`, and `units`. Each Unit has `id`, `subproblem_id`, `required_questions` (ID, importance, sufficient_when), `axes`, and `coverage_plan` (question ID and primary axis). A Unit may record its own positive `plan_version` (default: root version); releases, reviews, and results use that version so an independent Unit's revision need not restamp earlier unaffected results. Axes contain the fields in [axis design](axis-design.md): question, objective, assigned question IDs, scope, exclusions, differentiation, intentional overlap, evidence strategy, expected output, contribution, independent start, and assignment rationale. `round` defaults to 1; at most one new axis may have round 2. There is no fixed initial-axis cap.

Each Unit also records:

- `host_check: {status: pending|passed, plan_version: <released version>}`.
- `capacity: {investigation_slots: <available investigation capacity excluding Host/Orchestrator>}`.
- `plan_review: {required: <boolean>, triggers: [], status: not_required|pending|resolved|unresolved, plan_version: <reconciled version>, invocations: [], findings: []}`.

Triggers use axis-design codes. Each review invocation records `agent_id` and `tool_usage`; at most two are allowed on the same fresh-context general reviewer. Findings record ID, severity, resolution, and a nonempty `resolution_reason` for accepted/rejected findings. Preserve full input-grounded artifacts separately. Triggered review cannot be skipped; unresolved major/blocking findings block release. Before dispatch, Host release and required-review reconciliation must match current plan version; capacity must fit all initial axes. Recorded checks do not prove review quality, fresh context, user approval, or atomic slot reservation.

Result-state fields are `question_coverage` (question ID, status, claim IDs), `result_status`, `stop_reasons`, `unknowns`, and `objections`; these may be absent before report. An objection has ID, severity, resolution, and a reason when accepted/rejected. Accepting a blocking objection requires changing or withdrawing its conclusion; structure checks cannot prove that change sufficient.

For complex requests add `parent_questions` (ID and importance), `required_outcomes` (IDs), `subproblems` (ID, Unit ID, parent question IDs, outcome IDs, execution status, result status, validity), `dependencies` (from, to, type), `global_coverage` (question ID, primary Subproblem ID, outcome IDs, status, claim IDs, report location), and `global_result` (status, stop reasons, unknowns, objections). Units remain sequential.

## Work ledger and call usage

`ledger.json` contains `research_id`, `units` mapping Unit IDs to `initial_axis_ids`, optional `limits`, and `entries`, plus `request_usage`. Freeze initial IDs to match state round-1 axes. Default initial work is N and total investigation work is N+2. Other defaults: 2 rounds, 2 supplementary tasks, 1 Extra Explorer, 1 Critic, 1 retry, 1 Status Check. Each initial axis can be reserved/dispatched only once; new axes require Extra Explorer.

Each entry has ID, round, `kind` (`explore`, `extra_explore`, `verify`, `critic`, `retry`, `status_check`), target, state (`reserved`, `dispatched`, `finished`, `failed`, `cancelled`), and `tool_usage`. Record `dispatched_at` and `completed_at` where available. Only pre-dispatch cancellations with null dispatch time and nonempty `release_reason` release reservations. Dispatched failures/cancellations consume work and retain call usage. A scoped same-axis follow-up is a separate Round 2 verify entry, not a fresh initial allowance. All initial work must return or be recorded failed/cancelled before supplementary dispatch.

`tool_usage` is `{limit: <integer>, used: <integer>, calls: [{tool: <nonempty string>, purpose: <nonempty string>}]}`. Used equals log length and cannot exceed limit. Initial Explorer ceiling is 30; supplementary, Status Check, plan-review, and final consistency work each have a 10-call ceiling. Failed attempts and resumed turns count cumulatively. Exclusions and early-stop rules are in [evidence and evaluation](evidence-and-evaluation.md).

Stricter limits are valid. Higher work/call limits require `authorized_limit_override: true` and nonempty `authorization_reference` on the Unit (or standalone result); checks verify a reference is recorded, not that permission really occurred. Overrides never bypass frozen IDs or permit duplicate initial work. New IDs and follow-ups do not silently reset usage.

Reserve and check with `scripts/validate.py dispatch --state <state.json> --ledger <ledger.json> --unit <unit-id>`. Reservations are recorded serially by Orchestrator; actual work may overlap. Multiple Units cannot have recorded active investigation at once. For complex requests only, `request_usage.consistency_work_items` is at most 2, with matching `consistency_entries` (ID, state, and tool usage); reserved/active final work cannot overlap unfinished Unit work. These checks inspect records, not live scheduling/interception. Keep work-item and phase start/end timings when available.

## Results and reporting

An Explorer result has research ID, Unit ID, axis ID, plan version, `work_item_id`, `task_kind`, `tool_usage`, status, answer summary, claims, evidence, and question coverage. Copy usage to the ledger unchanged. Complete requires assigned questions answered; exhausted incomplete work is partial. Claims have ID, statement, kind, question IDs, supporting/contradicting evidence IDs, premise claim IDs, confidence, and confidence reason. Evidence has ID, source type, locator, location, origin ID, observation. Coverage has question ID, status, claim IDs. Scoped IDs use `<research-id>/<unit-id>/<axis-id>-C<number>` or `-E<number>`. Retain dates/revisions, applicability, limitations, unknowns, alternatives, and decisive counterevidence.

Use `result --state <state.json> --result <result.json> --ledger <ledger.json>` after copying usage to its work item; it reconciles identity, task kind, target axis, and usage. Without a safe ledger, omit that argument and record the linkage check as unrun; the validator emits a warning. Result checks fields, IDs, and links, not factual support. Report validates state/ledger, rejects complete before the initial cohort returns, unanswered critical questions, unresolved blocking objections, missing outcomes, or stale essential results. Pending/blocked Subproblems may have null local result status and are represented through global coverage; they cannot make an essential outcome complete. Partial/decision status needs stop reasons and a linked unresolved Unknown. Unfinished work cannot coexist with complete. The script emits ok/errors/warnings and exits nonzero on failure. Axis quality, log truth, source independence, evidence sufficiency, and user-choice classification remain agent judgments.
