"""Proof: flipping allow_plus_ones in Flagsmith changes the RSVP rule with no restart.

Usage, with the app running:  python -m scripts.prove_flag_flip http://localhost:8000
It saves one test RSVP for household 10 and leaves the flag as it found it.
"""
import sys
import time

import httpx

from app import flags

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
# A colleague household: no segment override, so it follows the environment default.
RSVP = {"household_id": 10, "attending": True, "headcount": 5, "plus_ones": 2, "diet": "veg"}


def try_rsvp() -> str:
    response = httpx.post(f"{BASE}/api/rsvp/text", json=RSVP, timeout=20)
    return "accepted" if response.status_code == 200 else response.json()["error"]


def flip_and_wait(enabled: bool, expected: str) -> None:
    start = time.perf_counter()
    flags.set_flag("allow_plus_ones", enabled)
    published = time.perf_counter() - start
    while (result := try_rsvp()) != expected and time.perf_counter() - start < 60:
        time.sleep(0.5)
    total = time.perf_counter() - start
    print(f"set_flag(allow_plus_ones, {enabled}): published in {published:.1f}s, "
          f"RSVP with 2 +1s is now '{result}' after {total:.1f}s")  # fmt: skip


original = flags.get_environment_flags()["allow_plus_ones"]["enabled"]
print(f"start: allow_plus_ones={original}, RSVP with 2 +1s: '{try_rsvp()}'")
try:
    flip_and_wait(True, "accepted")
    flip_and_wait(False, "plus_ones_not_allowed")
finally:
    flags.set_flag("allow_plus_ones", original)
    print(f"restored: allow_plus_ones={original}")
