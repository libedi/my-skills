"""Static packaging checks for every installable skill."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from install import available, manifest


MODEL_ID = re.compile(r"\b(?:gpt-\d|claude-(?:opus|sonnet|haiku))")
LINK = re.compile(r"\]\(([^)]+)\)")
CLAUDE_MODEL_ALIASES = {"opus", "sonnet", "haiku", "fable", "inherit"}
CLAUDE_MODEL_ID = re.compile(r"claude-[a-z0-9.-]+")
CLAUDE_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"Missing frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"Unclosed frontmatter: {path}") from error
    fields = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def check() -> None:
    for name in available():
        source, data = manifest(name)
        skill_fields = frontmatter(source / "SKILL.md")
        if skill_fields.get("name") != name or not skill_fields.get("description"):
            raise ValueError(f"Invalid SKILL.md identity: {name}")
        for path in [source / "SKILL.md", *(source / "references").glob("*.md")]:
            content = path.read_text(encoding="utf-8")
            if MODEL_ID.search(content):
                raise ValueError(f"Runtime model ID in shared instructions: {path}")
            for target in LINK.findall(content):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                if not resolved.is_relative_to(source.resolve()) or not resolved.exists():
                    raise ValueError(f"Broken or external package link in {path}: {target}")
        for relative in data["agents"]["codex"]:
            path = source / relative
            profile = tomllib.loads(path.read_text(encoding="utf-8"))
            if not all(profile.get(field) for field in ("name", "description", "model", "model_reasoning_effort", "developer_instructions")):
                raise ValueError(f"Incomplete Codex profile: {path}")
            if ".agents/skills/research" in profile["developer_instructions"]:
                raise ValueError(f"Repository-relative skill path: {path}")
        for relative in data["agents"]["claude"]:
            path = source / relative
            fields = frontmatter(path)
            if not all(fields.get(field) for field in ("name", "description", "model", "effort")):
                raise ValueError(f"Incomplete Claude profile: {path}")
            if fields["name"] != path.stem:
                raise ValueError(f"Claude profile name differs from file name: {path}")
            if fields["model"] not in CLAUDE_MODEL_ALIASES and not CLAUDE_MODEL_ID.fullmatch(fields["model"]):
                raise ValueError(f"Unknown Claude model {fields['model']!r}: {path}")
            if fields["effort"] not in CLAUDE_EFFORTS:
                raise ValueError(f"Unknown Claude effort {fields['effort']!r}: {path}")
    print(f"Portability checks passed for {len(available())} skill(s)")


if __name__ == "__main__":
    check()
