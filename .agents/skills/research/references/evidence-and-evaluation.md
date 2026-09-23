# Evidence, evaluation, and exit

## Claim-level evidence

Track each substantive claim as fact, inference, or proposal and link its question, supporting and contradicting evidence, premises, assumptions, applicability, confidence, and confidence reason. Evidence identifies source type, locator, location within the source, source date, access time, revision, original `origin_id`, direct observation, and limitations. Use IDs including request and Unit boundaries, for example `R-001/U1/A-C1` and `R-001/U1/A-E1`. Different webpages repeating one report share an `origin_id`. Unknown origin means independence is unconfirmed, not multiple corroborating sources.

Prefer original material and verify the relevant passage. A search snippet is not a checked source. Distinguish official claims from measured behavior, code possibilities from reproduced failures, and user statements from independently verified facts. Check date, version, geography, population, and conditions when they affect applicability. Record material counterevidence and how it changes the conclusion. Confidence is high, medium, or low with an explanation, not a calculated probability or source-count score. A single authoritative primary source can suffice for a narrow factual question.

A script can confirm that an evidence ID exists; it cannot confirm that the evidence supports the claim. The Orchestrator, and Critic when used, must read decisive source passages and check reasoning. Do not relabel an unsupported fact as inference merely to pass a structural check.

## Evaluate after Round 1

Check structure, source locations, duplicate origins, coverage of each required question against `sufficient_when`, direct support for decisive claims, conflicts and applicability, useful diversity, and the expected gain of more work. Similar answers alone do not justify an Extra Explorer. Choose the smallest response to a concrete gap:

| Gap | Next action |
|---|---|
| Missing critical question or alternative | Extra Explorer, once and within Round 2 |
| Missing primary passage, measurement, or reproduction | Evidence Verification |
| Weak premise or reasoning using existing evidence | Critic |
| Contradictory facts | Compare original source, date, version, and conditions; verify if necessary |
| User preference changes the choice | Conditional alternatives or a decision request via Host |
| Sufficient answer | Synthesis; do not spend remaining budget automatically |

Count substantial follow-up research by the Orchestrator as a supplementary task too. A short location check is ordinary evaluation; a new source family or hypothesis is investigation.

## Unknowns and final status

An Unknown records ID, related question/claim, importance, state, reason, and next check. States: `verified` (with evidence), `assumption` (with effect if wrong), `unresolved`, `inaccessible`, or `human_decision`. An empirical fact missing because of access or budget is not a user preference. Do not treat silence as a decision.

Use `complete` only when all critical questions meet their sufficiency criteria, required outcomes are satisfied, decisive claims are adequately supported, no blocking objection remains, and essential complex results are current. A supporting unknown may remain if its effect is bounded. Use `partial` for missing empirical evidence, budget/access failure, or unresolved blocking review. Use `needs_user_decision` when a choice is essential and conditional reporting does not fulfill the request. These last two states are not ordered; record other contributing causes too. Exit reasons include `sufficient`, `budget_exhausted`, `access_limited`, `execution_failed`, `unresolved_objection`, `low_expected_gain`, `user_cancelled`, and `user_input_required`.

Lead the report with the answer and status, then decisive evidence near each claim, applicability and alternatives, counterevidence, unresolved questions, next checks, method and limitations, validation outcome, and source list. Short reports may omit irrelevant sections but must keep status, decisive support, and material limits. Report that a check was unrun when no safe files or runtime were available. Do not disclose private source copies or raw internal reasoning. The Host checks user intent and delivers the result.
