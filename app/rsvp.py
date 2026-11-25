"""RSVP rules, shared by every channel so voice cannot bypass what text enforces."""
from typing import Literal

from pydantic import BaseModel, Field

from app import db, flags

Diet = Literal["veg", "non_veg", "jain", "mixed"]


class Rsvp(BaseModel):
    attending: bool
    headcount: int = Field(ge=0, le=200)  # invited people who are coming
    plus_ones: int = Field(default=0, ge=0, le=100)  # extra people on top of headcount
    diet: Diet = "mixed"


class RsvpRejected(Exception):
    """Becomes a JSON error response in main.py."""

    def __init__(self, status: int, code: str, message: str, **extra):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.extra = extra  # more fields for the response, such as what voice heard


def household_flags(household: dict) -> dict:
    return flags.get_identity_flags(household["id"], {"segment": household["segment"]})


def find_household(household_id: int) -> dict:
    household = db.get_household(household_id)
    if household is None:
        raise RsvpRejected(404, "household_not_found", f"No household with id {household_id}.")
    return household


def submit(
    household_id: int,
    rsvp: Rsvp,
    channel: str,
    transcript: str | None = None,
    state: dict | None = None,  # the household's flags, if the caller already read them
) -> dict:
    household = find_household(household_id)

    headcount, plus_ones = 0, 0
    if rsvp.attending:
        # Anyone above the invited count is a +1, even if the guest calls them family.
        uninvited = max(0, rsvp.headcount - household["invited_count"])
        headcount = rsvp.headcount - uninvited
        plus_ones = rsvp.plus_ones + uninvited
        if headcount + plus_ones == 0:
            raise RsvpRejected(422, "empty_rsvp", "Attending, but nobody is coming. How many people?")

    if plus_ones > 0:
        state = state or household_flags(household)
        if state["catering_lock_mode"]["enabled"]:
            raise RsvpRejected(
                409, "catering_locked", "The catering count is now final, so we cannot add extra guests."
            )
        if not state["allow_plus_ones"]["enabled"]:
            raise RsvpRejected(
                409,
                "plus_ones_not_allowed",
                f"This invite is for {household['invited_count']} people and cannot include extra guests.",
            )

    return db.save_rsvp(
        household_id, rsvp.attending, headcount, plus_ones, rsvp.diet, channel, transcript
    )
