# Agent contracts

## Role and context boundary

The Host owns the original request, permission boundaries, user questions, and final delivery. The Research Orchestrator is one fresh-context custom subagent for the whole request. It owns Briefs, decomposition, axes, dispatch, ledger, evaluation, and local/global synthesis. Explorer and Critic are scoped workers. Only the Orchestrator may delegate one level. When nested delegation is unavailable, the Host dispatches an exact assignment as a sibling and returns the unchanged result. The Host must not insert a favored hypothesis or alter research evidence.

The Intake Packet carries `original_request` verbatim, confirmed user decisions with their provenance, hard constraints, relevant source locations, available capabilities, and budget. Prior conversation facts must be marked fact, user statement, or assumption. Do not include earlier tentative conclusions or raw conversation history. Use a fresh start such as `fork_turns="none"` when available. The Orchestrator custom agent profile must actually load `gpt-6-astra` and `high`, or a user-approved replacement. File existence does not prove activation.

## Research Brief

For each Unit record `research_id`, `subproblem_id`, `unit_id`, `plan_version`, `problem` (intent, scope, as-of, output), `constraints` (hard and preferences), `goals`, `hypotheses`, `required_outcomes`, `known_facts` with evidence IDs, `user_statements`, `assumptions`, `required_questions`, `evaluation_criteria`, `available_capabilities`, `limitations`, and `budget`. Each required question has a stable ID, `importance` of `critical` or `supporting`, and a `sufficient_when` criterion based on direct evidence, applicability, and counterexamples rather than source count.

Give every initial Explorer the same Brief version, its own axis, common criteria, evidence rules, and time/permission bounds. Do not send another initial Explorer's intermediate result. The project profiles are `research_explorer` (`gpt-6-sol`, `medium`) and `research_critic` (`gpt-6-sol`, `high`). Select and verify the relevant profile when supported; otherwise set model and reasoning effort explicitly per assignment and record actual values. Profile existence alone does not prove activation. Explorer may research its axis, report out-of-scope findings, and write only to permitted result paths. It cannot broaden scope, modify original material, contact others, or spawn agents.

Explorer returns the full JSON result in [JSON contracts](json-contracts.md): claims, evidence, question coverage, alternatives or hypotheses when relevant, unknowns, search log, limitations, and decisive counterevidence. `status: complete` only means its assigned task ended. If the result is large or multiple axes run, write it under `research/<run-id>/results/<unit-id>-<axis-id>.json` and return a short summary with the path and decisive findings. If safe writing is unavailable, return the complete result inline and mark file checks unrun. The Orchestrator must inspect the full result for claims that drive the conclusion.

## Critic and Status Check

Use Critic only after a provisional conclusion exists and a meaningful inference gap, contested premise, conflicting evidence, or high-stakes adversarial check warrants it. Give the Brief, provisional conclusion, relevant claims/evidence, counterevidence, budget, and precise review target. Return objections with stable IDs, target claim IDs, `blocking`/`major`/`minor` severity, issue, evidence or counterexample, impact, and needed resolution. Separate confirmed flaws from possibilities. The Orchestrator resolves each objection as `accepted`, `rejected_with_evidence`, or `unresolved` with a reason. A Critic is not automatically authoritative.

A Status Check is optional once per Unit when the Orchestrator proposes `complete` without a Critic. It examines only existing evidence and the draft against required questions and `sufficient_when`. It returns `supported`, `weakly_supported`, or `unsupported` by question with reasons. It does not search for new sources or alternatives and is counted outside the five investigation tasks but inside total usage. Lack of an independent context must be disclosed.

## Handoff and failure

When a user decision is needed, the Orchestrator sends the Host the choice, alternatives, and effect; the Host asks the user. Silence is not approval. On cancellation or tool failure, keep valid partial evidence, ledger use, and limits. Do not claim independent verification from sequential work by one agent. The Host delivers only after comparing the report with the original request and seeing the validation status.
