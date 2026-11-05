# Claude Code runtime adapter

Install the skill and all three agent definitions together. The logical Research Orchestrator, Explorer, and Critic map to the custom subagent types `research-orchestrator`, `research-explorer`, and `research-critic`. Their frontmatter is the single source for Claude model and effort choices. Pass the installed skill's absolute path in every assignment; no definition assumes a repository-relative path. Claude Code picks up edited definitions within seconds, but the first file in a new `agents` directory needs a session restart.

## Starting and resuming agents

- Start each role with the Agent tool and its custom `subagent_type`. A custom subagent starts with a fresh context: its own system prompt, the assignment, CLAUDE.md files, and environment metadata, but not the caller's conversation.
- Never use the `fork` subagent type or `/subtask` for a research role. A fork inherits the whole conversation, which is context contamination.
- Omit the Agent tool's `model` and `effort` parameters. A passed value overrides the frontmatter.
- The Host's conditional plan reviewer is the built-in `general-purpose` subagent type, not a fork.
- Resume an idle Orchestrator or Explorer with `SendMessage` addressed to its agent ID. The resumed agent keeps its history, and its usage stays cumulative.
- CLAUDE.md is still loaded into each subagent. It is project configuration, not conversation history; put any CLAUDE.md rule that should constrain research into the Intake Packet as a hard constraint rather than relying on it.

## Settings that override the definitions

Before starting the Orchestrator, check the environment and the `env` block of Claude Code settings. If any of these is set, an observed mismatch is likely and must be resolved with the user before the Harness runs:

- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` with `CLAUDE_CODE_SUBAGENT_MODEL`: every subagent uses that model and ignores frontmatter.
- `CLAUDE_CODE_EFFORT_LEVEL`: overrides every subagent's effort.
- An `availableModels` allowlist or `deniedModels` entry that excludes the definition's model.

Alias remapping such as `ANTHROPIC_DEFAULT_SONNET_MODEL` or `modelOverrides` changes which model an alias selects; the inspector below catches a remap to another model family.

`CLAUDE_CODE_SUBAGENT_MODEL` without force is only a fallback and does not override frontmatter.

## Verifying applied settings

The Agent tool result does not report the applied model or effort, but Claude Code writes each subagent's transcript locally. Run the bundled inspector from the installed skill directory with the agent ID the Agent tool returned:

```sh
python adapters/claude/scripts/inspect_agent.py <agent-id> --definition adapters/claude/agents/<role>.md
```

It compares the transcript's agent type, model, and effort with the definition and prints JSON. Status `ok` is a runtime-observed match. Status `mismatch` exits 1 and blocks the run as an observed mismatch; an agent type of `fork` or another role means the wrong agent was started. Status `unverified` means the transcript or a field was not found and is disclosed rather than treated as a mismatch. The transcript layout is not a documented interface; it was observed in Claude Code 2.1.296. Set `--projects-dir` when `CLAUDE_CONFIG_DIR` relocates `~/.claude`.

The Host inspects the Orchestrator before releasing investigation. The Orchestrator inspects each Explorer and Critic after it returns. In the sibling fallback, the Host inspects the sibling and forwards the report unchanged with the result.

The inspector also lists the agent's actual tool calls with their targets in order. A resumed agent appends to the same transcript, so the list is cumulative across turns. The Orchestrator compares that list with the worker's self-reported `tool_usage`, and records any difference that the evidence contract's exclusions, such as setup reads of skill contracts, do not explain. Classifying which calls are research-tool calls remains a judgment governed by the evidence contract.

## Delegation depth and tool limits

By default Claude Code allows three levels of subagents below the main conversation, so Host → Orchestrator → Explorer or Critic fits. With `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`, the Orchestrator receives no Agent tool; it then gives the Host exact sibling assignments and receives unchanged results.

The Orchestrator keeps the Agent and `SendMessage` tools. Explorer and Critic are denied Agent, so they cannot delegate further, and `SendMessage`, so initial Explorers cannot exchange findings with siblings. Both are denied Edit and NotebookEdit. Explorer keeps Write for its result file. Critic is denied Write and returns objections inline. Tools a host product adds outside Claude Code's built-in set are governed by the role instructions, not by the denylist.
