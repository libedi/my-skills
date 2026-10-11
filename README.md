# my-skills

Reusable agent skills live under `skills/`. The skill package is the source of truth; runtime discovery folders are installation targets.

| Skill | Purpose |
| --- | --- |
| [research](skills/research/SKILL.md) | Evidence-backed research using an Orchestrator, independent Explorers, and optional Critic. |

Run `python scripts/install.py` to list installable skills. Python 3.11 or newer is required for the installer and validator.

```sh
# Install into the current project.
python scripts/install.py --skill research --target codex --scope project
python scripts/install.py --skill research --target claude --scope project

# Install for this user, or select an explicit destination root.
python scripts/install.py --skill research --target codex --scope user
python scripts/install.py --skill research --target claude --scope project --root /path/to/project

# Remove only an explicitly selected managed installation.
python scripts/install.py --uninstall --skill research --target codex --scope project
```

Codex installs the skill in `.agents/skills/` and agent profiles in `.codex/agents/`; Claude Code uses `.claude/skills/` and `.claude/agents/`. User scope uses the corresponding folders under the home directory. The default installation copies the complete self-contained skill package. `--mode link` creates source links for repository dogfooding; on Windows, symbolic links may require Developer Mode or permission to create links. Reinstall by uninstalling the managed copy first. The installer refuses to overwrite existing destinations or uninstall an agent profile edited after installation.

Install the skill and its profiles together. The runtime-specific role mapping and settings are in [Codex adapter guidance](skills/research/adapters/codex/runtime.md) and [Claude adapter guidance](skills/research/adapters/claude/runtime.md). Claude Code needs a session restart after the installer creates the first file in a new `.claude/agents` directory. The Claude adapter includes a transcript inspector that checks each subagent's applied model, effort, and tool calls. The historical [design document](docs/research-harness-design/research-harness-design.md) explains the original Codex design but is not required at runtime.
