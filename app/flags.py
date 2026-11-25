"""Flagsmith wrapper. Reads flags with the server-side environment key."""
import logging

from flagsmith import Flagsmith

from app.config import FLAGSMITH_SERVER_ENVIRONMENT_KEY

log = logging.getLogger(__name__)

_client = (
    Flagsmith(environment_key=FLAGSMITH_SERVER_ENVIRONMENT_KEY)
    if FLAGSMITH_SERVER_ENVIRONMENT_KEY
    else None
)

# Why the last read fell back to its default, or None if it really came from Flagsmith.
last_error: str | None = None


def is_enabled(feature: str, default: bool = False) -> bool:
    global last_error
    if _client is None:
        last_error = "FLAGSMITH_SERVER_ENVIRONMENT_KEY is not set"
        return default
    try:
        enabled = _client.get_environment_flags().is_feature_enabled(feature)
        last_error = None
        return enabled
    except Exception as exc:
        last_error = f"{type(exc).__name__}: {exc}"
        log.warning("Flagsmith read of %s failed: %s", feature, last_error)
        return default
