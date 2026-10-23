#!/usr/bin/env python3
"""Shared only-lower time budget for whole-minor checker observations."""

import math
import os

CHECK_MINOR_TOTAL_SECONDS = 360.0  # seven member shares plus bounded shared observations


def check_minor_seconds() -> float:
    """The total budget; a caller with a shorter limit (the turn-end gate) may lower it, never raise it."""
    try:
        requested = float(os.environ.get("NEXUS_CHECK_MINOR_BUDGET_SECONDS", CHECK_MINOR_TOTAL_SECONDS))
    except ValueError:
        return CHECK_MINOR_TOTAL_SECONDS
    if math.isnan(requested):
        return CHECK_MINOR_TOTAL_SECONDS
    return min(CHECK_MINOR_TOTAL_SECONDS, max(1.0, requested))
