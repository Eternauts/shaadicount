"""Flagsmith wrapper. Reads flags with the server-side environment key."""
from flagsmith import Flagsmith

from app.config import FLAGSMITH_SERVER_KEY

_client = Flagsmith(environment_key=FLAGSMITH_SERVER_KEY) if FLAGSMITH_SERVER_KEY else None


def is_enabled(feature: str, default: bool = False) -> bool:
    if _client is None:
        return default
    try:
        return _client.get_environment_flags().is_feature_enabled(feature)
    except Exception:
        return default
