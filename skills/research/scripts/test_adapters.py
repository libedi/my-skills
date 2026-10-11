"""Role policies that the research skill relies on runtime adapters to enforce."""

import json
import tomllib
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ROLES = ("research-orchestrator", "research-explorer", "research-critic")
WORKERS = ("research-explorer", "research-critic")


def claude_definition(role: str) -> dict[str, str]:
    lines = (SKILL / "adapters" / "claude" / "agents" / f"{role}.md").read_text(encoding="utf-8").splitlines()
    fields = {}
    for line in lines[1 : lines.index("---", 1)]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def tool_list(value: str | None) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}


class ClaudeAdapterPolicyTests(unittest.TestCase):
    def test_manifest_installs_every_role(self):
        manifest = json.loads((SKILL / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(Path(item).stem for item in manifest["agents"]["claude"]),
            sorted(ROLES),
        )

    def test_definition_names_match_roles(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertEqual(claude_definition(role)["name"], role)

    def test_workers_cannot_delegate_or_message_siblings(self):
        for role in WORKERS:
            with self.subTest(role=role):
                denied = tool_list(claude_definition(role).get("disallowedTools"))
                self.assertLessEqual({"Agent", "SendMessage", "Edit", "NotebookEdit"}, denied)

    def test_explorer_can_write_its_result_but_critic_cannot(self):
        self.assertNotIn("Write", tool_list(claude_definition("research-explorer").get("disallowedTools")))
        self.assertIn("Write", tool_list(claude_definition("research-critic").get("disallowedTools")))

    def test_orchestrator_keeps_delegation_and_resume_tools(self):
        fields = claude_definition("research-orchestrator")
        self.assertFalse(tool_list(fields.get("disallowedTools")) & {"Agent", "SendMessage"})
        allowed = tool_list(fields.get("tools"))
        if allowed:
            self.assertLessEqual({"Agent", "SendMessage"}, allowed)

    def test_effort_matches_codex_profile_for_each_role(self):
        for role in ROLES:
            with self.subTest(role=role):
                codex = tomllib.loads((SKILL / "adapters" / "codex" / "agents" / f"{role}.toml").read_text(encoding="utf-8"))
                self.assertEqual(claude_definition(role)["effort"], codex["model_reasoning_effort"])

    def test_inspector_referenced_by_adapter_exists(self):
        inspector = "adapters/claude/scripts/inspect_agent.py"
        self.assertTrue((SKILL / inspector).is_file())
        self.assertIn(inspector, (SKILL / "adapters" / "claude" / "agents" / "research-orchestrator.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
