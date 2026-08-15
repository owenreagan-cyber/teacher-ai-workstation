"""Phase 24 Predictive Teacher Brain package.

Importing this package re-exports only pure contracts. Prediction logic lives in
``rule_engine`` and entrypoints ``predict_week`` / ``validate_prediction``, which
must be imported explicitly when execution is required.
"""

from .models import *  # noqa: F401,F403
