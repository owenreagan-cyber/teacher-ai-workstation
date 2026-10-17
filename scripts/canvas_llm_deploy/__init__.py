"""Guarded Canvas deployment for the Teacher AI Workstation weekly intake.

This package is the FIRST component that may reach Canvas mutation code. It
follows: READY_TO_PUBLISH -> preflight -> explicit owner confirmation -> ordered
writes -> post-write readback -> PUBLISHED_VERIFIED.

It is deliberately kept OUTSIDE ``scripts/canvas_llm_intake/`` because that
package carries a static zero-write proof. This package imports FROM the intake
package (one direction only) and delegates Canvas I/O to the existing canonical
write helpers in ``scripts/canvas_llm_phase22/`` (never forks them).
"""
from __future__ import annotations

__version__ = "1.0.0"
