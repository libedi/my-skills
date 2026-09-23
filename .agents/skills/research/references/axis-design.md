# Decomposition and exploration axes

A Subproblem is a cohesive question needing its own answer. A Research Unit is one execution of planning, investigation, evaluation, and synthesis for that Subproblem. An Exploration Axis is a distinct investigable question inside a Unit. Evaluation Criteria compare findings across axes. Do not call all three a topic. A request with many viewpoints but one conclusion may still be one Unit.

## First plan

The Orchestrator drafts the first plan before receiving the Host's preferred interpretation. For complex requests, map each parent critical question and required deliverable to a Subproblem and specify dependencies. For each Unit:

1. Frame the purpose, object, boundaries, user hard constraints, and unverified premises.
2. Extract dimensions that could change the answer and separately list common evaluation criteria. A dimension is not automatically a worker.
3. Generate candidate axes as questions with likely evidence paths.
4. Merge candidates whose question, evidence, and output are effectively identical. Keep deliberate overlap when it independently tests a decisive fact or applies common criteria.
5. Assign every required question a primary axis; check for unmapped critical questions and deliverables.
6. Check whether axes can start without another axis's findings. Merge dependent axes or schedule a follow-up.
7. Select at most three initial axes; use one for small problems. Record why splitting helps, or why it does not.

An axis record needs `id`, `question`, `objective`, `required_question_ids`, `scope`, `exclude`, `distinct_from`, `intentional_overlap`, `evidence_strategy`, and `expected_output`. A coverage plan maps each required question to `primary_axis` and optional `cross_check_axes`. Plan coverage and actual result coverage are different records. The Host checks the initial plan against the exact user request for missing requirements, altered hard constraints, unwarranted scope, and duplicate axes. It should not force its preferred answer into the plan. Record the first plan and any revision reason.

Use dimension patterns as candidate generators, never a fixed three-role template: factual work may separate source definition, period/population differences, and counterevidence; causal work may separate competing mechanisms, confounders, and disconfirming tests; alternatives may separate minimal change, structural alternative, and operating failure; reviews may separate requirements gaps, feasibility, and failure behavior. Different axes may reach the same conclusion for good evidentiary reasons.

## Escape Axis

Consider a Round 2 Extra Explorer only if a critical question is uncovered, all alternatives rest on the same unverified premise, or evidence reveals a genuinely new direction. First test whether similar results reflect strong common evidence. Keep user hard constraints intact. Identify which assumption the Escape Axis relaxes or tests, what new explanation it may reveal, and its limitations. It consumes the single Extra Explorer allowance and one of two supplementary tasks; never create a third round to bypass the budget.
