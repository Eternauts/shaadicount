"""Flagsmith: reads with the server key, changes with the Admin API."""
import logging

import httpx
from flagsmith import Flagsmith
from flagsmith.exceptions import FlagsmithFeatureDoesNotExistError

from app.config import (
    FLAGSMITH_ADMIN_TOKEN,
    FLAGSMITH_ENVIRONMENT_API_KEY,
    FLAGSMITH_SERVER_ENVIRONMENT_KEY,
)

log = logging.getLogger(__name__)

ADMIN_API = "https://api.flagsmith.com/api/v1"

# Used when Flagsmith has never answered. +1s fail closed: bad wifi must not unlock them.
DEFAULTS = {
    "allow_plus_ones": {"enabled": False, "value": None},
    "catering_lock_mode": {"enabled": False, "value": None},
    "voice_fallback_text": {"enabled": False, "value": None},
    "rsvp_prompt_variant": {"enabled": False, "value": "direct"},
}

_client = (
    Flagsmith(environment_key=FLAGSMITH_SERVER_ENVIRONMENT_KEY, request_timeout_seconds=3)
    if FLAGSMITH_SERVER_ENVIRONMENT_KEY
    else None
)
_last_good: dict[str, dict] = {}  # last answer per household, for when the network drops

# Why the last read did not come from Flagsmith, or None if it did.
last_error: str | None = None


def _read(key: str, fetch) -> dict:
    """Live flags if possible, else the last known ones, else DEFAULTS."""
    global last_error
    try:
        if _client is None:
            raise RuntimeError("FLAGSMITH_SERVER_ENVIRONMENT_KEY is not set")
        answer = fetch()
        state = {}
        for name, default in DEFAULTS.items():
            try:
                flag = answer.get_flag(name)
                state[name] = {"enabled": flag.enabled, "value": flag.value}
            except FlagsmithFeatureDoesNotExistError:
                log.warning("flag %s does not exist in Flagsmith, using its default", name)
                state[name] = default
        last_error = None
        _last_good[key] = state
        return state
    except Exception as exc:
        last_error = f"{type(exc).__name__}: {exc}"
        log.warning("Flagsmith read for %s failed: %s", key, last_error)
        return _last_good.get(key, DEFAULTS)


def get_environment_flags() -> dict:
    """The defaults everyone gets, before segments and A/B splits."""
    return _read("environment", lambda: _client.get_environment_flags())


def get_identity_flags(household_id: int, traits: dict) -> dict:
    """Flags for one household. Flagsmith matches the traits against its segments."""
    identifier = f"household-{household_id}"
    return _read(identifier, lambda: _client.get_identity_flags(identifier, traits=traits))


def get_value(feature: str, household_id: int, traits: dict) -> str:
    """A flag's value for one household. A flag that is off gives the default value."""
    flag = get_identity_flags(household_id, traits)[feature]
    return flag["value"] if flag["enabled"] and flag["value"] else DEFAULTS[feature]["value"]


class FlagUpdateError(Exception):
    """A flag could not be changed. main.py turns this into JSON."""


def set_flag(feature_name: str, enabled: bool) -> None:
    """Switch a flag's environment default on or off. Segment overrides stay as they are.

    The environment uses Feature Versioning v2, so a change means publishing a new version.
    """
    if not FLAGSMITH_ADMIN_TOKEN or not FLAGSMITH_ENVIRONMENT_API_KEY:
        raise FlagUpdateError("FLAGSMITH_ADMIN_TOKEN or the environment key is not set")
    headers = {"Authorization": f"Api-Key {FLAGSMITH_ADMIN_TOKEN}"}
    try:
        # Publishing a version can take several seconds.
        with httpx.Client(base_url=ADMIN_API, headers=headers, timeout=15) as client:
            found = client.get(
                f"/environments/{FLAGSMITH_ENVIRONMENT_API_KEY}/featurestates/",
                params={"feature_name": feature_name},
            )
            found.raise_for_status()
            # Only the environment default, never a segment or identity override.
            states = [
                s for s in found.json()["results"]
                if s["feature_segment"] is None and s["identity"] is None
            ]  # fmt: skip
            if len(states) != 1:
                raise FlagUpdateError(f"Expected one state for {feature_name}, found {len(states)}")
            current = states[0]
            if current["enabled"] != enabled:
                environment = client.get(f"/environments/{FLAGSMITH_ENVIRONMENT_API_KEY}/")
                environment.raise_for_status()
                url = f"/environments/{environment.json()['id']}/features/{current['feature']}/versions/"
                client.post(
                    url,
                    json={
                        "publish_immediately": True,
                        "feature_states_to_update": [
                            {
                                "feature_segment": None,
                                "enabled": enabled,
                                # Required by the API, so send the current value back unchanged.
                                "feature_state_value": {
                                    "type": "unicode",
                                    "string_value": current["feature_state_value"],
                                },
                            }
                        ],
                    },
                ).raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Status only: the exception text holds the full URL.
        status = exc.response.status_code
        raise FlagUpdateError(f"Flagsmith Admin API returned HTTP {status}") from None
    except httpx.HTTPError as exc:
        raise FlagUpdateError(f"Could not reach Flagsmith ({type(exc).__name__})") from None
    log.info("flag %s set to %s", feature_name, enabled)
