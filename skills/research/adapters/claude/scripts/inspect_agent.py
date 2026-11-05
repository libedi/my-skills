"""Report a Claude Code subagent's observed type, model, effort, and tool calls from its local transcript.

The transcript layout is not a documented interface. It was observed in Claude Code 2.1.296:
``<projects>/<project>/<session>/subagents/agent-<id>.meta.json`` holds ``agentType``,
``parentAgentId``, and ``spawnDepth``; ``agent-<id>.jsonl`` assistant entries hold
``message.model`` and ``effort``. Anything absent is reported as unverified, never as a mismatch.
Exit status is 1 only for an observed mismatch.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

AGENT_ID = re.compile(r"^[A-Za-z0-9_-]+$")
ALIASES = {"opus", "sonnet", "haiku", "fable"}
TARGET_KEYS = ("file_path", "notebook_path", "path", "url", "query", "pattern", "command")
TARGET_LIMIT = 200


def default_projects_dir() -> Path:
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(config) if config else Path.home() / ".claude") / "projects"


def locate(agent_id: str, projects: Path) -> tuple[Path, Path] | None:
    if not AGENT_ID.match(agent_id):
        raise ValueError(f"Invalid agent ID: {agent_id!r}")
    candidates = sorted(
        projects.glob(f"*/*/subagents/agent-{agent_id}.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    transcript = candidates[0]
    return transcript, transcript.with_name(f"agent-{agent_id}.meta.json")


def expectations_from(definition: Path) -> dict[str, str]:
    """Read the required name, model, and effort from an agent definition's frontmatter."""
    lines = definition.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError(f"Missing frontmatter: {definition}")
    fields = {}
    for line in lines[1 : lines.index("---", 1)]:
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    mapping = {"expect_type": "name", "expect_model": "model", "expect_effort": "effort"}
    return {option: fields[field] for option, field in mapping.items() if fields.get(field)}


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def target_of(tool_input: object) -> str:
    if isinstance(tool_input, dict):
        for key in TARGET_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value[:TARGET_LIMIT]
    return ""


def read_transcript(transcript: Path) -> tuple[list[str], list[str], list[dict[str, str]]]:
    models, efforts, calls = [], [], []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message") or {}
        if message.get("model"):
            models.append(message["model"])
        if entry.get("effort"):
            efforts.append(entry["effort"])
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls.append({"tool": block.get("name", ""), "target": target_of(block.get("input"))})
    return unique(models), unique(efforts), calls


def model_matches(expected: str, observed: str) -> bool:
    if expected in ALIASES:
        return f"-{expected}-" in f"-{observed}-"
    return observed == expected


def compare(observed: list[str], expected: str, matches) -> str:
    if not observed:
        return "unverified"
    return "match" if all(matches(expected, value) for value in observed) else "mismatch"


def inspect(
    agent_id: str,
    projects: Path,
    expect_type: str | None = None,
    expect_model: str | None = None,
    expect_effort: str | None = None,
) -> dict:
    located = locate(agent_id, projects)
    report: dict = {"agent_id": agent_id, "found": located is not None}
    checks: dict[str, str] = {}
    if located is None:
        report["status"] = "unverified"
        report["reason"] = f"No transcript for agent {agent_id} under {projects}"
        return report

    transcript, meta_path = located
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    models, efforts, calls = read_transcript(transcript)
    report.update(
        transcript=str(transcript),
        agent_type=meta.get("agentType"),
        parent_agent_id=meta.get("parentAgentId"),
        spawn_depth=meta.get("spawnDepth"),
        models=models,
        efforts=efforts,
        tool_call_count=len(calls),
        tool_calls=calls,
    )
    if expect_type:
        observed_type = [meta["agentType"]] if meta.get("agentType") else []
        checks["agent_type"] = compare(observed_type, expect_type, str.__eq__)
    if expect_model:
        checks["model"] = "unverified" if expect_model == "inherit" else compare(models, expect_model, model_matches)
    if expect_effort:
        checks["effort"] = compare(efforts, expect_effort, str.__eq__)

    report["checks"] = checks
    if "mismatch" in checks.values():
        report["status"] = "mismatch"
    elif "unverified" in checks.values():
        report["status"] = "unverified"
    else:
        report["status"] = "ok"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("agent_id", help="Agent ID returned when the subagent was started")
    parser.add_argument("--projects-dir", type=Path, default=default_projects_dir())
    parser.add_argument("--definition", type=Path, help="Agent definition whose name, model, and effort are required")
    parser.add_argument("--expect-type", help="Expected agent type; overrides --definition")
    parser.add_argument("--expect-model", help="Expected model alias, full model ID, or inherit; overrides --definition")
    parser.add_argument("--expect-effort", help="Expected effort; overrides --definition")
    args = parser.parse_args()
    expected = expectations_from(args.definition) if args.definition else {}
    for option in ("expect_type", "expect_model", "expect_effort"):
        if getattr(args, option):
            expected[option] = getattr(args, option)
    report = inspect(args.agent_id, args.projects_dir.expanduser(), **expected)
    json.dump(report, sys.stdout, indent=2)
    print()
    return 1 if report["status"] == "mismatch" else 0


if __name__ == "__main__":
    sys.exit(main())
