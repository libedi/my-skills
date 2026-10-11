# Kiro runtime adapter

Install the skill and all three agent definitions together. The logical Research Orchestrator, Explorer, and Critic map to the custom agents `research-orchestrator`, `research-explorer`, and `research-critic`. This adapter targets Kiro IDE 1.x and Kiro CLI 3.x, where `toolsSettings` is replaced by `permissions`. The definitions use the JSON form of the agent schema, which both load from `.kiro/agents/`. Pass the installed skill's absolute path in every assignment; no definition assumes a repository-relative path.

| Role | Model | Requested effort |
| --- | --- | --- |
| research-orchestrator | `claude-opus-5.5` | `high` |
| research-explorer | `claude-sonnet-5.5` | `medium` |
| research-critic | `claude-sonnet-5.5` | `high` |

The agent JSON `model` field is the single source for models; the table repeats it and a test keeps them equal. Model IDs available to an organization differ, so confirm them with `/model` and change the adapter JSON in the skill source before installing; the installer will not uninstall an agent file edited after installation. Claude Opus 5.5 and Sonnet 5.5 are Experimental in Kiro, and an organization's model governance may not offer them; Claude Opus 5 and Sonnet 5 are the Active alternatives. If a model is unavailable, the first prompt to that agent fails; treat that as inability to select the required profile.

## Effort is not selectable per agent

Kiro custom agents have no effort field. Effort comes from the session (`/effort`, `/model`, `--effort`) or from per-model defaults in `chat.modelDefaults`, so roles that share a model cannot receive different efforts. This table is the single source for requested effort. Record the requested value for each role, record the applied value as unverified unless the runtime shows it, and disclose that Kiro does not apply effort per role. This disclosure alone does not block the Harness; an observed mismatch in a value the runtime does show still does.

## Starting agents

- The Host starts each role through Kiro's subagent mechanism by naming the custom agent, for example "Use the research-orchestrator agent to …". A request naming an unknown agent fails rather than falling back to the default agent.
- A subagent runs with an isolated conversation history. Steering files, MCP servers, workspace files, and permission settings are shared. Steering is project configuration, not conversation history; put any steering rule that should constrain research into the Intake Packet as a hard constraint rather than relying on it.
- The Host's conditional plan reviewer is Kiro's default subagent without a custom agent.
- Only the Orchestrator has the `subagent` tool. Its `permissions` rules allow the `subagent` capability for `research-explorer` and `research-critic` without a prompt and deny every other agent. Explorer and Critic have no `subagent` tool, so they cannot delegate further.

## Continuation instead of resume

Kiro documents no way to resume a finished subagent, and a subagent task graph cannot change once it starts. A research run therefore uses one Orchestrator instance per phase, linked by run files rather than by agent ID:

1. **Planning instance.** The Host starts `research-orchestrator` with the Intake Packet, the skill path, and a new run ID. It writes `research/<run-id>/state.json` and `handoff.md`, returns the first plan and review triggers, and stops.
2. **Host check.** The Host checks the plan against the original request and starts the plan reviewer when required, as in the skill.
3. **Continuation instance.** The Host starts a new `research-orchestrator` with the same Intake Packet, the run directory, and only request-linked discrepancies, unchanged review output, confirmed user decisions, execution limits, or a version-specific release. It reads the run files before anything else and keeps every recorded usage. Repeat for each later Host follow-up.

`handoff.md` holds what the next instance needs and the state does not: open decisions, pending objections, and why the plan has its current shape. It is research state, not Host conversation. Record each instance's start and phase with the runtime selection record. Disclose that the run used continuation instances; do not describe them as one resumed agent.

If safe file storage is unavailable, the Orchestrator returns the state inline and the Host passes it unchanged to the next instance.

The plan reviewer cannot be resumed either. When the Orchestrator's revision needs the one targeted recheck, the Host starts a new default subagent as a continuation of the first review. It passes the first review's full unchanged output, the plan version that review saw, and the revised plan, and asks for a check of those findings and the revisions they caused only. The Host saves the first review output under `research/<run-id>/reviews/`. The Orchestrator records the recheck with its own agent ID, `continuation_of` set to the first reviewer's agent ID, and `prior_review` set to that saved file; the validator rejects a different reviewer without both. There is still at most one recheck, and a third reviewer is never started.

Workers follow the same rule. A Kiro worker cannot be resumed, so a same-axis verification starts a new `research-explorer` with the earlier result file labelled as prior work. It is recorded as a supplementary verify task and carries forward the original usage. Dispatch the initial cohort as one batch without dependencies, and supplementary work as a later batch.

## Depth and the sibling fallback

Kiro does not document whether a subagent can start its own subagents. If the Orchestrator's subagent tool is missing or fails to start a worker, it returns exact sibling assignments. The Host starts those workers by name, collects their unchanged results into `research/<run-id>/results/`, and starts a continuation instance to evaluate them.

## Permission rules

A subagent inherits its parent session's rules, combined with its own by deny-wins intersection: a `deny` anywhere wins, then `ask`, then `allow`, and an action no rule covers prompts for approval. The Host session's user and workspace `permissions.yaml` therefore apply to every role, and the Orchestrator's rules apply to its workers. A Host-level `ask` or `deny` overrides the allow rules below and can stall or block a parallel cohort; resolve that with the user before releasing investigation.

Because rules are inherited, the Orchestrator is narrowed through its `tools`, not through `deny` rules that would also bind its workers. Its only `deny` rules cover writes outside `./research/` and agents other than the two workers, which no worker needs.

The Orchestrator has `read`, `write`, `shell`, and `subagent` and nothing else. `write` keeps `state.json`, `ledger.json`, `handoff.md`, and the report, which continuation instances depend on. `shell` runs the bundled validator without a prompt; any other command prompts. It has no `web` or MCP tools: Kiro's `web` tag covers search as well as fetch, and a `deny` on search would be inherited by Explorers, so the Orchestrator cannot be limited to reopening cited sources. It judges evidence from worker results and local files, and sends an independent re-read of a decisive source to `research-critic` as a Status Check or Critic task. Disclose when a decisive web or connector source was checked only through worker observations.

Every role's rules allow file reads and web search and fetch without a prompt; on the Orchestrator these rules exist only so that its workers inherit an `allow`. Orchestrator and Explorer may write only under `./research/`; a `deny` rule covers every other workspace path. Critic has no write tool and returns objections inline. Explorer's shell is limited to read-only inspection commands such as `git log`, `grep`, and `cat`; other commands are denied. Critic has no shell. Shell patterns match command prefixes, so arguments such as output redirection are not inspected. These rules narrow what the role instructions already forbid; they do not prove that no file outside `research/` changed.

## Verification status

Kiro does not document a way to observe a subagent's applied model or effort or its actual tool calls. Record applied values as unverified and treat `tool_usage` as self-reported. The open runtime questions and a probe to answer them are in the repository's `docs/runtime-probes/kiro.md`; that document is not needed at runtime.
