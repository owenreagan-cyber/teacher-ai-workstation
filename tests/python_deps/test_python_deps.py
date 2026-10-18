"""One-line missing-dependency errors (scripts/python_deps.py).

Run: python3.12 -m unittest discover -s tests/python_deps -p 'test_*.py'
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import python_deps  # noqa: E402


def _hide(name: str):
    """Make ``import name`` fail as if the package were not installed."""
    real = python_deps.importlib.import_module

    def fake(module, *args, **kwargs):
        if module == name or module.startswith(name + "."):
            raise ModuleNotFoundError(f"No module named {name!r}")
        return real(module, *args, **kwargs)

    return mock.patch.object(python_deps.importlib, "import_module", side_effect=fake)


class RequireTest(unittest.TestCase):
    def test_installed_package_is_returned(self) -> None:
        self.assertIs(python_deps.require("json"), sys.modules["json"])

    def test_missing_yaml_is_one_line_with_install_command(self) -> None:
        with _hide("yaml"), self.assertRaises(python_deps.MissingDependencyError) as ctx:
            python_deps.require("yaml")
        msg = str(ctx.exception)
        self.assertNotIn("\n", msg)
        self.assertIn("PyYAML is not installed", msg)
        py = f"python{sys.version_info.major}.{sys.version_info.minor}"
        self.assertIn(f"Install it with: {py} -m pip install --user --break-system-packages pyyaml", msg)

    def test_missing_pymupdf_names_package(self) -> None:
        with _hide("pymupdf"), self.assertRaises(python_deps.MissingDependencyError) as ctx:
            python_deps.require("pymupdf")
        self.assertIn("PyMuPDF is not installed", str(ctx.exception))
        self.assertIn("pip install --user --break-system-packages pymupdf", str(ctx.exception))

    def test_is_system_exit_so_cli_prints_no_traceback(self) -> None:
        self.assertTrue(issubclass(python_deps.MissingDependencyError, SystemExit))
        code = ("import sys; sys.path.insert(0, %r); from scripts import python_deps; "
                "python_deps.require('taw_definitely_missing_pkg')") % str(REPO)
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(len(proc.stderr.strip().splitlines()), 1, proc.stderr)
        self.assertIn("taw_definitely_missing_pkg is not installed", proc.stderr)

    def test_yaml_loaders_fail_clearly_instead_of_json_fallback(self) -> None:
        from scripts.curriculum_production import lesson_sequence
        from scripts.lesson_blueprint import content_budgets

        with _hide("yaml"):
            with self.assertRaises(python_deps.MissingDependencyError):
                lesson_sequence.load_sequence_catalog()
            with self.assertRaises(python_deps.MissingDependencyError):
                content_budgets.load_content_budgets()


if __name__ == "__main__":
    unittest.main()
