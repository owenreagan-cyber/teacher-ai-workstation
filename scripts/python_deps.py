"""One-line errors for missing third-party Python packages.

Code that needs PyYAML or PyMuPDF (and the artifact-quality extras) imports
them through ``require`` so a missing package stops the run with a single line
naming the package and the install command, instead of a traceback or a
misleading ``JSONDecodeError`` from a JSON fallback.

    yaml = require("yaml")
    pymupdf = require("pymupdf")
"""
from __future__ import annotations

import importlib
import sys
from types import ModuleType

# import name -> (package name people know, pip name)
PACKAGES = {
    "yaml": ("PyYAML", "pyyaml"),
    "pymupdf": ("PyMuPDF", "pymupdf"),
    "PIL": ("Pillow", "pillow"),
    "docx": ("python-docx", "python-docx"),
    "pptx": ("python-pptx", "python-pptx"),
}


class MissingDependencyError(SystemExit):
    """Exit with a one-line message (no traceback) when a package is missing.

    A ``SystemExit`` subclass so a command-line run prints only the message
    and exits 1; it also carries the message for test runners and callers.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


def install_command(pip_name: str) -> str:
    python = f"python{sys.version_info.major}.{sys.version_info.minor}"
    return f"{python} -m pip install --user --break-system-packages {pip_name}"


def missing_message(module: str) -> str:
    label, pip_name = PACKAGES.get(module, (module, module))
    python = f"python{sys.version_info.major}.{sys.version_info.minor}"
    return (f"{label} is not installed for {python} ({sys.executable}). "
            f"Install it with: {install_command(pip_name)}")


def require(module: str) -> ModuleType:
    """Import ``module`` or exit with a one-line install hint."""
    try:
        return importlib.import_module(module)
    except ImportError:
        raise MissingDependencyError(missing_message(module)) from None
