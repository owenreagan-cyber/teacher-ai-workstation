"""Phase 18D pure contracts package (import-safe).

Importing this package re-exports only pure write-intent contracts. Dry-run
assembly, snapshot modeling, and safety-diff logic live in ``deployment``,
``snapshot``, and ``diff`` respectively, imported explicitly when needed.
"""

from .contracts import *  # noqa: F401,F403
