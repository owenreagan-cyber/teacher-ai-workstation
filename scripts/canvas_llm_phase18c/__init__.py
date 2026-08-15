"""Phase 18C read-only Teacher Preview assembly package.

Importing this package re-exports only pure contracts. Preview assembly lives in
``preview`` and drift detection in ``drift``, imported explicitly when needed.
"""

from .contracts import *  # noqa: F401,F403
