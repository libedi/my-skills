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


def kiro_definition(role: str) -> dict:
    return json.loads((SKILL / "adapters" / "kiro" / "agents" / f"{role}.json").read_text(encoding="utf-8"))


def kiro_requested_efforts() -> dict[str, str]:
    """Kiro has no per-agent effort field, so runtime.md's role table is the single source."""
    efforts = {}
    for line in (SKILL / "adapters" / "kiro" / "runtime.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip(" `") for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in ROLES:
            efforts[cells[0]] = cells[2]
    return efforts


def rules_for_all(definition: dict) -> list[dict]:
    return definition.get("permissions", {}).get("rules", [])


def rules_for(definition: dict, capability: str) -> list[dict]:
    return [rule for rule in definition.get("permissions", {}).get("rules", []) if rule.get("capability") == capability]


class KiroAdapterPolicyTests(unittest.TestCase):
    def test_manifest_installs_every_role(self):
        manifest = json.loads((SKILL / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(Path(item).stem for item in manifest["agents"]["kiro"]), sorted(ROLES))

    def test_definition_names_match_roles(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertEqual(kiro_definition(role)["name"], role)

    def test_only_orchestrator_can_spawn_and_only_research_workers(self):
        orchestrator = kiro_definition("research-orchestrator")
        self.assertIn("subagent", orchestrator["tools"])
        spawn = rules_for(orchestrator, "subagent")
        self.assertIn({"capability": "subagent", "match": sorted(WORKERS), "effect": "allow"}, spawn)
        self.assertIn({"capability": "subagent", "match": ["*"], "exclude": sorted(WORKERS), "effect": "deny"}, spawn)
        for role in WORKERS:
            with self.subTest(role=role):
                tools = set(kiro_definition(role)["tools"])
                self.assertFalse(tools & {"subagent", "@builtin", "*"})

    def test_no_settings_removed_in_cli_v3(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertFalse(set(kiro_definition(role)) & {"toolsSettings", "allowedTools", "toolAliases", "keyboardShortcut"})

    def test_orchestrator_is_a_coordinator_without_research_tools(self):
        self.assertEqual(set(kiro_definition("research-orchestrator")["tools"]), {"read", "write", "shell", "subagent"})
        self.assertFalse(kiro_definition("research-orchestrator").get("includeMcpJson"))

    def test_orchestrator_denies_nothing_its_workers_need(self):
        # Kiro subagents inherit the parent's rules by deny-wins intersection.
        denied = {rule["capability"] for rule in rules_for_all(kiro_definition("research-orchestrator")) if rule["effect"] == "deny"}
        self.assertLessEqual(denied, {"fs_write", "subagent"})

    def test_critic_has_no_write_tool(self):
        self.assertNotIn("write", kiro_definition("research-critic")["tools"])

    def test_orchestrator_and_explorer_write_only_under_research(self):
        for role in ("research-orchestrator", "research-explorer"):
            with self.subTest(role=role):
                rules = rules_for(kiro_definition(role), "fs_write")
                self.assertIn({"capability": "fs_write", "match": ["./research/**"], "effect": "allow"}, rules)
                self.assertIn({"capability": "fs_write", "match": ["./**"], "exclude": ["./research/**"], "effect": "deny"}, rules)

    def test_requested_effort_matches_codex_profile_for_each_role(self):
        efforts = kiro_requested_efforts()
        for role in ROLES:
            with self.subTest(role=role):
                codex = tomllib.loads((SKILL / "adapters" / "codex" / "agents" / f"{role}.toml").read_text(encoding="utf-8"))
                self.assertEqual(efforts.get(role), codex["model_reasoning_effort"])

    def test_role_table_model_matches_definition(self):
        for line in (SKILL / "adapters" / "kiro" / "runtime.md").read_text(encoding="utf-8").splitlines():
            cells = [cell.strip(" `") for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0] in ROLES:
                with self.subTest(role=cells[0]):
                    self.assertEqual(cells[1], kiro_definition(cells[0])["model"])


if __name__ == "__main__":
    unittest.main()
