import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from install import REPO, destinations, install, manifest, uninstall


class InstallTests(unittest.TestCase):
    def test_no_selection_lists_skills_without_installing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = subprocess.run(
                [sys.executable, str(REPO / "scripts" / "install.py")],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("Available skills: research", result.stdout)
            self.assertFalse((root / ".agents").exists())

    def test_copy_install_and_uninstall_both_runtimes(self):
        source, data = manifest("research")
        for target in ("codex", "claude"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                install(root, target, ["research"], "copy")
                skill, agents = destinations(root, target, "research", data)
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertTrue((skill / "scripts" / "validate.py").is_file())
                self.assertEqual(len(agents), 3)
                self.assertTrue(all(destination.is_file() for _, destination in agents))
                self.assertEqual((skill / "SKILL.md").read_bytes(), (source / "SKILL.md").read_bytes())
                uninstall(root, target, ["research"])
                self.assertFalse(skill.exists())
                self.assertTrue(all(not destination.exists() for _, destination in agents))

    def test_collision_does_not_overwrite(self):
        _, data = manifest("research")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill, agents = destinations(root, "codex", "research", data)
            agents[0][1].parent.mkdir(parents=True)
            agents[0][1].write_text("user profile", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                install(root, "codex", ["research"], "copy")
            self.assertFalse(skill.exists())
            self.assertEqual(agents[0][1].read_text(encoding="utf-8"), "user profile")

    def test_uninstall_refuses_modified_agent(self):
        _, data = manifest("research")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            install(root, "codex", ["research"], "copy")
            skill, agents = destinations(root, "codex", "research", data)
            agents[0][1].write_text("edited", encoding="utf-8")
            with self.assertRaises(ValueError):
                uninstall(root, "codex", ["research"])
            self.assertTrue(skill.exists())

    def test_link_install_when_symlinks_available(self):
        source, data = manifest("research")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            try:
                install(root, "codex", ["research"], "link")
            except OSError as error:
                self.skipTest(f"Symbolic links unavailable: {error}")
            skill, agents = destinations(root, "codex", "research", data)
            self.assertTrue(skill.is_symlink())
            self.assertEqual(skill.resolve(), source.resolve())
            self.assertTrue(all(destination.is_symlink() for _, destination in agents))
            uninstall(root, "codex", ["research"])
            self.assertFalse(skill.exists())


if __name__ == "__main__":
    unittest.main()
