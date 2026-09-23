# Complex requests

Use this path when separate cohesive question groups need separate conclusions or deliverables, or a later question depends on an earlier result. A single question examined from several directions uses multiple axes in one Unit. One isolated Research Orchestrator owns the whole request; do not create an Orchestrator per Subproblem.

## Parent plan and dependencies

Preserve the original user request and every required outcome. Map each parent critical question and deliverable to a primary Subproblem, possible supporting Subproblems, a sufficiency condition, and eventual report location. A cross-cutting concern gets an owner, contributing Units, and sufficiency condition; it is not automatically another Unit. Run `validate.py plan` before investigation and check that the mapping has not silently dropped a requirement.

Represent a dependency by source and target Subproblem, type (`factual`, `decision`, or `shared_source`), required claim/decision IDs, readiness condition, and input version. Shared use of a source alone does not impose order. When dependencies cycle, merge coupled questions, extract a common prior question, or use bounded conditional scenarios. If unresolved, mark affected Units blocked and explain why. Run only one Unit at a time; independent axes within the active Unit may run in parallel. Use one ledger and preserve cumulative counts.

A predecessor may be partial yet provide the exact input a successor needs. A predecessor may be complete yet not supply a required user decision. Send only necessary claim/evidence/decision IDs, applicability, confidence reasons, unresolved objections, and version to later Units. Label fact, inference, assumption, recommendation, and user decision separately. A recommendation does not become another Unit's hard constraint; use an explicit conditional scenario if needed.

## Change and synthesis

Each Subproblem tracks `execution_status` (pending, running, blocked, finished), `result_status` (null before a result; otherwise complete, partial, needs_user_decision), and `validity` (current or stale). On changed evidence, decision, or version, follow direct and transitive dependencies, mark affected results stale, and recheck only impacted questions. Reopen the same Unit with remaining Round 2 and task budget. Never create a new ID to reset limits. New Subproblems are allowed only for a real omission within the user's scope; record reason, parent questions, scope delta, expected work, and plan version. Ask the user only if scope or user-set limits must change.

Compare parent questions and required outcomes, hard constraints, shared source versions, ownership gaps, incompatible recommendations, and tradeoffs across Local Synthesis results. Use existing evidence for ordinary comparison. New evidence or substantial review consumes remaining Unit budget or, if exhausted or cross-Unit by nature, one of at most two request-wide consistency tasks. Charge each task to one budget and count it once in total usage. Do not start a new investigation loop from the final consistency allowance.

Global `complete` requires all parent critical questions and required outcomes satisfied, essential results current, and decisive cross-Unit conflicts resolved or explained through valid conditional alternatives. A nonessential partial Unit may coexist with global complete if its effect is bounded. All Units being complete does not imply global complete. `partial` covers essential uninvestigated, blocked, stale, unsupported, or conflicted work. `needs_user_decision` requires a genuinely indispensable choice. Report valid partial findings even when other Units cannot run. The Host checks the global answer against the original request before delivery.
