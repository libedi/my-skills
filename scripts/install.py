"""Install one or more repository skills into Codex or Claude Code discovery paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
MARKER = ".my-skills-install.json"
DISCOVERY = {"codex": (".agents", ".codex"), "claude": (".claude", ".claude")}


def manifest(name: str) -> tuple[Path, dict]:
    if not name or not all(char.islower() or char.isdigit() or char == "-" for char in name):
        raise ValueError(f"Invalid skill name: {name!r}")
    source = SKILLS / name
    data = json.loads((source / "install.json").read_text(encoding="utf-8"))
    if data.get("name") != name or not (source / "SKILL.md").is_file():
        raise ValueError(f"Invalid manifest for {name}")
    for files in data.get("agents", {}).values():
        for item in files:
            relative = Path(item)
            if relative.is_absolute() or ".." in relative.parts or not (source / relative).is_file():
                raise ValueError(f"Invalid agent path in {name}: {item}")
    return source, data


def available() -> list[str]:
    return sorted(path.parent.name for path in SKILLS.glob("*/install.json"))


def destinations(root: Path, target: str, name: str, data: dict) -> tuple[Path, list[tuple[Path, Path]]]:
    if target not in data.get("agents", {}):
        raise ValueError(f"Skill {name} does not support {target}")
    skill_dir, agent_dir = DISCOVERY[target]
    installed_skill = root / skill_dir / "skills" / name
    agents = [
        (SKILLS / name / relative, root / agent_dir / "agents" / Path(relative).name)
        for relative in data["agents"][target]
    ]
    return installed_skill, agents


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(root: Path, target: str, names: list[str], mode: str) -> None:
    plans = []
    occupied = set()
    for name in names:
        source, data = manifest(name)
        installed_skill, agents = destinations(root, target, name, data)
        for path in [installed_skill, *(destination for _, destination in agents)]:
            if path in occupied or path.exists() or path.is_symlink():
                raise FileExistsError(f"Destination already exists: {path}")
            occupied.add(path)
        plans.append((name, source, installed_skill, agents))

    created: list[Path] = []
    try:
        for name, source, installed_skill, agents in plans:
            installed_skill.parent.mkdir(parents=True, exist_ok=True)
            if mode == "link":
                installed_skill.symlink_to(source, target_is_directory=True)
            else:
                shutil.copytree(source, installed_skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
            created.append(installed_skill)
            records = {}
            for original, destination in agents:
                destination.parent.mkdir(parents=True, exist_ok=True)
                if mode == "link":
                    destination.symlink_to(original)
                else:
                    shutil.copy2(original, destination)
                created.append(destination)
                records[destination.name] = digest(original)
            if mode == "copy":
                (installed_skill / MARKER).write_text(
                    json.dumps({"skill": name, "target": target, "agents": records}, indent=2) + "\n",
                    encoding="utf-8",
                )
            print(f"Installed {name} for {target} at {installed_skill}")
    except Exception:
        for path in reversed(created):
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        raise


def uninstall(root: Path, target: str, names: list[str]) -> None:
    plans = []
    for name in names:
        source, data = manifest(name)
        installed_skill, agents = destinations(root, target, name, data)
        if installed_skill.is_symlink():
            if installed_skill.resolve() != source.resolve():
                raise ValueError(f"Skill link points elsewhere: {installed_skill}")
            for original, destination in agents:
                if not destination.is_symlink() or destination.resolve() != original.resolve():
                    raise ValueError(f"Agent link was changed: {destination}")
            mode = "link"
        else:
            marker = installed_skill / MARKER
            if not marker.is_file():
                raise ValueError(f"Not a managed installation: {installed_skill}")
            record = json.loads(marker.read_text(encoding="utf-8"))
            if record.get("skill") != name or record.get("target") != target:
                raise ValueError(f"Installation marker mismatch: {marker}")
            expected = {destination.name for _, destination in agents}
            if set(record.get("agents", {})) != expected:
                raise ValueError(f"Agent list changed: {marker}")
            for _, destination in agents:
                if not destination.is_file() or digest(destination) != record["agents"][destination.name]:
                    raise ValueError(f"Agent was changed: {destination}")
            mode = "copy"
        plans.append((name, installed_skill, agents, mode))

    for name, installed_skill, agents, mode in plans:
        for _, destination in agents:
            destination.unlink()
        if mode == "link":
            installed_skill.unlink()
        else:
            shutil.rmtree(installed_skill)
        print(f"Uninstalled {name} for {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--skill", action="append", help="Skill to install; repeat for more than one")
    selection.add_argument("--all", action="store_true", help="Install every available skill")
    parser.add_argument("--target", choices=DISCOVERY)
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--root", type=Path, help="Project directory or user home; defaults to cwd or home")
    parser.add_argument("--mode", choices=("copy", "link"), default="copy")
    parser.add_argument("--uninstall", action="store_true", help="Remove only explicitly selected managed skills")
    args = parser.parse_args()

    if not args.skill and not args.all:
        print("Available skills: " + ", ".join(available()))
        return
    if args.uninstall and (args.all or not args.skill):
        parser.error("--uninstall requires one or more --skill selections")
    if not args.target:
        parser.error("--target is required for install and uninstall")
    names = available() if args.all else list(dict.fromkeys(args.skill))
    unknown = set(names) - set(available())
    if unknown:
        parser.error("Unknown skills: " + ", ".join(sorted(unknown)))
    root = (args.root or (Path.cwd() if args.scope == "project" else Path.home())).expanduser().resolve()
    if args.uninstall:
        uninstall(root, args.target, names)
    else:
        install(root, args.target, names, args.mode)


if __name__ == "__main__":
    main()
