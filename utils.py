"""Minimal safe_json_loads stub for Mintabie."""

import json
import logging

logger = logging.getLogger(__name__)


def safe_json_loads(text: str) -> dict | None:
    """Safely parse JSON, returning None on failure."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.debug("safe_json_loads: failed to parse JSON")
        return None
