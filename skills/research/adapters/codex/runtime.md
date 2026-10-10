# Codex runtime adapter

Install the skill and all three agent profiles together. The logical Research Orchestrator, Explorer, and Critic map to `research_orchestrator`, `research_explorer`, and `research_critic`. The profile TOML files are the single source for Codex model and effort choices. Pass the installed skill's absolute path to every dispatched role; profile instructions do not assume a repository-relative path.

Start the Orchestrator with a fresh history (`fork_turns="none"` when available) and only the Intake Packet. Record the requested profile, model, effort, and fresh-history option. Inspect spawn output for effective values. In a 2026-10-10 Codex desktop probe, spawn output contained only the agent ID; an absent effective value is recorded as unverified and disclosed to the user, not treated as a mismatch. Stop if a mismatch or inherited prior conversation is actually observed. Apply the same rule to Explorer and Critic. If a configured role cannot be selected, do not silently inherit the parent's model.

The Orchestrator may delegate one level. If nested delegation is unavailable, it gives the Host an exact sibling assignment and receives the unchanged result.
