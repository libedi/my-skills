import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inspect_agent import expectations_from, inspect

SCRIPT = Path(__file__).resolve().parent / "inspect_agent.py"


def assistant(model, effort, *tools):
    content = [{"type": "tool_use", "name": name, "input": tool_input} for name, tool_input in tools]
    return {
        "type": "assistant",
        "agentId": "a1",
        "requestedModel": model,
        "effort": effort,
        "message": {"model": model, "content": content or [{"type": "text", "text": "done"}]},
    }


class TranscriptFixture:
    def __init__(self, root: Path):
        self.projects = root / "projects"

    def add(self, agent_id, meta, entries, session="s1"):
        directory = self.projects / "-work-project" / session / "subagents"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"agent-{agent_id}.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        with (directory / f"agent-{agent_id}.jsonl").open("w", encoding="utf-8") as stream:
            stream.write(json.dumps({"type": "user", "agentId": agent_id, "message": {"role": "user", "content": "assignment"}}) + "\n")
            for entry in entries:
                stream.write(json.dumps(entry) + "\n")


EXPLORER_META = {"agentType": "research-explorer", "parentAgentId": "orch1", "spawnDepth": 2}


class InspectAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.fixture = TranscriptFixture(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def run_inspect(self, agent_id="a1", **expected):
        return inspect(agent_id, self.fixture.projects, **expected)

    def test_missing_transcript_is_unverified_not_mismatch(self):
        report = self.run_inspect(expect_model="sonnet")
        self.assertEqual(report["status"], "unverified")
        self.assertFalse(report["found"])

    def test_reports_identity_and_effective_settings(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-sonnet-5-5", "medium")])
        report = self.run_inspect()
        self.assertTrue(report["found"])
        self.assertEqual(report["agent_type"], "research-explorer")
        self.assertEqual(report["parent_agent_id"], "orch1")
        self.assertEqual(report["spawn_depth"], 2)
        self.assertEqual(report["models"], ["claude-sonnet-5-5"])
        self.assertEqual(report["efforts"], ["medium"])

    def test_matching_alias_type_and_effort_pass(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-sonnet-5-5", "medium")])
        report = self.run_inspect(expect_type="research-explorer", expect_model="sonnet", expect_effort="medium")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["checks"], {"agent_type": "match", "model": "match", "effort": "match"})

    def test_full_model_id_must_match_exactly(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-sonnet-5-5", "medium")])
        self.assertEqual(self.run_inspect(expect_model="claude-sonnet-5-5")["checks"]["model"], "match")
        self.assertEqual(self.run_inspect(expect_model="claude-sonnet-5")["checks"]["model"], "mismatch")

    def test_inherited_parent_model_is_mismatch(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-opus-5-5", "medium")])
        report = self.run_inspect(expect_model="sonnet")
        self.assertEqual(report["status"], "mismatch")
        self.assertEqual(report["checks"]["model"], "mismatch")

    def test_any_turn_on_another_model_or_effort_is_mismatch(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-sonnet-5-5", "medium"), assistant("claude-sonnet-5-5", "low")])
        report = self.run_inspect(expect_effort="medium")
        self.assertEqual(report["efforts"], ["medium", "low"])
        self.assertEqual(report["checks"]["effort"], "mismatch")

    def test_fork_or_other_type_is_mismatch(self):
        self.fixture.add("a1", {**EXPLORER_META, "agentType": "fork"}, [assistant("claude-sonnet-5-5", "medium")])
        self.assertEqual(self.run_inspect(expect_type="research-explorer")["checks"]["agent_type"], "mismatch")

    def test_absent_effort_field_is_unverified(self):
        entry = assistant("claude-sonnet-5-5", None)
        del entry["effort"]
        self.fixture.add("a1", EXPLORER_META, [entry])
        report = self.run_inspect(expect_model="sonnet", expect_effort="medium")
        self.assertEqual(report["checks"], {"model": "match", "effort": "unverified"})
        self.assertEqual(report["status"], "unverified")

    def test_inherit_cannot_be_checked(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-sonnet-5-5", "medium")])
        self.assertEqual(self.run_inspect(expect_model="inherit")["checks"]["model"], "unverified")

    def test_tool_calls_are_logged_in_order_with_target(self):
        self.fixture.add(
            "a1",
            EXPLORER_META,
            [
                assistant("claude-sonnet-5-5", "medium", ("Read", {"file_path": "/skill/references/agent-contracts.md"})),
                assistant(
                    "claude-sonnet-5-5",
                    "medium",
                    ("WebSearch", {"query": "spring modulith events"}),
                    ("WebFetch", {"url": "https://example.com/doc", "prompt": "summarize"}),
                ),
                assistant("claude-sonnet-5-5", "medium", ("mcp__drive__search", {"q": "x"})),
            ],
        )
        report = self.run_inspect()
        self.assertEqual(report["tool_call_count"], 4)
        self.assertEqual(
            report["tool_calls"],
            [
                {"tool": "Read", "target": "/skill/references/agent-contracts.md"},
                {"tool": "WebSearch", "target": "spring modulith events"},
                {"tool": "WebFetch", "target": "https://example.com/doc"},
                {"tool": "mcp__drive__search", "target": ""},
            ],
        )

    def test_agent_id_cannot_escape_projects_directory(self):
        with self.assertRaises(ValueError):
            self.run_inspect("../../etc/passwd")

    def test_expectations_can_come_from_agent_definition(self):
        definition = Path(self.temp.name) / "research-explorer.md"
        definition.write_text("---\nname: research-explorer\nmodel: sonnet\neffort: medium\n---\nbody\n", encoding="utf-8")
        self.assertEqual(
            expectations_from(definition),
            {"expect_type": "research-explorer", "expect_model": "sonnet", "expect_effort": "medium"},
        )

    def test_cli_uses_definition_and_explicit_flags_override_it(self):
        definition = Path(self.temp.name) / "research-explorer.md"
        definition.write_text("---\nname: research-explorer\nmodel: sonnet\neffort: medium\n---\n", encoding="utf-8")
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-sonnet-5-5", "high")])
        command = [sys.executable, str(SCRIPT), "a1", "--projects-dir", str(self.fixture.projects), "--definition", str(definition)]
        from_definition = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(json.loads(from_definition.stdout)["checks"], {"agent_type": "match", "model": "match", "effort": "mismatch"})
        overridden = subprocess.run([*command, "--expect-effort", "high"], capture_output=True, text=True)
        self.assertEqual(json.loads(overridden.stdout)["status"], "ok")

    def test_cli_exit_code_reflects_mismatch_only(self):
        self.fixture.add("a1", EXPLORER_META, [assistant("claude-opus-5-5", "medium")])
        command = [sys.executable, str(SCRIPT), "--projects-dir", str(self.fixture.projects)]
        mismatch = subprocess.run([*command, "a1", "--expect-model", "sonnet"], capture_output=True, text=True)
        self.assertEqual(mismatch.returncode, 1)
        self.assertEqual(json.loads(mismatch.stdout)["status"], "mismatch")
        missing = subprocess.run([*command, "absent", "--expect-model", "sonnet"], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 0)
        self.assertEqual(json.loads(missing.stdout)["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
