# Claude Code runtime adapter

The logical Research Orchestrator, Explorer, and Critic map to `research-orchestrator`, `research-explorer`, and `research-critic`. Their frontmatter is the single source for Claude model and effort choices. Pass the installed skill's absolute path in every assignment; no profile assumes a repository-relative path.

Start a fresh custom subagent with only the Intake Packet. Check tool output for applied model and effort if the runtime exposes them. If it does not, record the requested values as unverified and disclose that limitation. Stop on an observed mismatch or inherited prior conversation. Do not infer effective settings from frontmatter alone.

The Orchestrator needs the `Agent` tool for one level of delegation. Explorer and Critic exclude it. If a runtime depth setting disables nested agents, the Orchestrator gives the Host exact sibling assignments. Claude Code model allowlists and environment effort overrides can change effective settings; inspect visible warnings when available.
