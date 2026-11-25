"""Flagsmith: reads with the server key, changes with the Admin API."""
import logging
import time

import httpx
from flagsmith import Flagsmith
from flagsmith.exceptions import FlagsmithFeatureDoesNotExistError

from app.config import (
    FLAGSMITH_ADMIN_TOKEN,
    FLAGSMITH_ENVIRONMENT_API_KEY,
    FLAGSMITH_SERVER_ENVIRONMENT_KEY,
)

log = logging.getLogger(__name__)
logging.getLogger("flagsmith").setLevel(logging.CRITICAL)  # a full traceback per missed refresh

ADMIN_API = "https://api.flagsmith.com/api/v1"
REFRESH_SECONDS = 3
STALE_SECONDS = 20
CATCH_UP_SECONDS = 20

# Used only until Flagsmith first answers. +1s fail closed: bad wifi must not unlock them.
DEFAULTS = {
    "allow_plus_ones": {"enabled": False, "value": None},
    "catering_lock_mode": {"enabled": False, "value": None},
    "voice_fallback_text": {"enabled": False, "value": None},
    "rsvp_prompt_variant": {"enabled": False, "value": "direct"},
}


class _Client(Flagsmith):
    """Remembers when the rules were last refreshed, so the dashboard can say if they are live."""

    refreshed_at: float | None = None

    def update_environment(self) -> None:
        before = getattr(self, "_environment", None)
        super().update_environment()  # on failure it keeps the rules it already has
        if self._environment is not before:
            self.refreshed_at = time.monotonic()


# Local evaluation: rules are fetched in the background and applied in memory. An RSVP never
# waits for Flagsmith, and a dropped connection cannot change a decision.
_client = (
    _Client(
        environment_key=FLAGSMITH_SERVER_ENVIRONMENT_KEY,
        request_timeout_seconds=5,
        enable_local_evaluation=True,
        environment_refresh_interval_seconds=REFRESH_SECONDS,
    )
    if FLAGSMITH_SERVER_ENVIRONMENT_KEY
    else None
)


# Flagsmith can serve the old rules for some seconds after a change. The lock must act at once,
# so for that long the value we just published wins.
_lock_set_to = False
_lock_set_until = 0.0


def problem() -> str | None:
    """Why the flags might not be current, or None if they are live."""
    if _client is None:
        return "FLAGSMITH_SERVER_ENVIRONMENT_KEY is not set"
    if _client.refreshed_at is None:
        return "Flagsmith has not answered yet"
    age = time.monotonic() - _client.refreshed_at
    return f"Last refreshed {age:.0f} s ago" if age > STALE_SECONDS else None


def _read(fetch) -> dict:
    try:
        # Without rules in memory the SDK would call the API and block, so use DEFAULTS instead.
        if _client is None or _client.refreshed_at is None:
            raise RuntimeError(problem())
        answer = fetch()
    except Exception as exc:
        log.warning("Flagsmith read failed, using safe defaults: %s", exc)
        return DEFAULTS
    state = {}
    for name, default in DEFAULTS.items():
        try:
            flag = answer.get_flag(name)
            state[name] = {"enabled": flag.enabled, "value": flag.value}
        except FlagsmithFeatureDoesNotExistError:
            log.warning("flag %s does not exist in Flagsmith, using its default", name)
            state[name] = default
    if time.monotonic() < _lock_set_until:
        state["catering_lock_mode"] = {**state["catering_lock_mode"], "enabled": _lock_set_to}
    return state


def get_environment_flags() -> dict:
    """The defaults everyone gets, before segments and A/B splits."""
    return _read(lambda: _client.get_environment_flags())


def get_identity_flags(household_id: int, traits: dict) -> dict:
    """Flags for one household. Flagsmith matches the traits against its segments."""
    return _read(lambda: _client.get_identity_flags(f"household-{household_id}", traits=traits))


def get_value(feature: str, state: dict) -> str:
    """A flag's value from a household's flags. A flag that is off gives the default value."""
    flag = state[feature]
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
                                # A version replaces all of this, so send the current value
                                # and A/B split back unchanged.
                                "feature_state_value": {
                                    "type": "unicode",
                                    "string_value": current["feature_state_value"],
                                },
                                "multivariate_feature_state_values": [
                                    {
                                        "multivariate_feature_option": v["multivariate_feature_option"],
                                        "percentage_allocation": v["percentage_allocation"],
                                    }
                                    for v in current["multivariate_feature_state_values"]
                                ],
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
    if _client is not None:
        _client.update_environment()  # do not wait for the next background refresh
    log.info("flag %s set to %s", feature_name, enabled)


def set_catering_lock(locked: bool) -> None:
    global _lock_set_to, _lock_set_until
    set_flag("catering_lock_mode", locked)
    _lock_set_to, _lock_set_until = locked, time.monotonic() + CATCH_UP_SECONDS
