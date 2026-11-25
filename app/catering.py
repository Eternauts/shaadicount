"""Turns RSVPs into the number the caterer cares about."""
import csv
import io

from app import db
from app.config import CATERER_BUFFER_PLATES, COST_PER_PLATE_INR


def impact() -> dict:
    households = db.list_households()
    attending = [h for h in households if h["status"] == "confirmed"]
    pending = [h for h in households if h["status"] == "pending"]

    confirmed = sum(h["headcount"] + h["plus_ones"] for h in attending)
    # Until a household answers, plan for everyone it was invited to bring.
    expected = sum(h["invited_count"] for h in pending)
    predicted = confirmed + expected
    overflow = max(0, predicted - CATERER_BUFFER_PLATES)

    return {
        "invited_plates": sum(h["invited_count"] for h in households),
        "confirmed_plates": confirmed,
        "confirmed_plus_ones": sum(h["plus_ones"] for h in attending),
        "expected_from_pending": expected,
        "pending_households": len(pending),
        "predicted_plates": predicted,
        "buffer_plates": CATERER_BUFFER_PLATES,
        "overflow_plates": overflow,
        "cost_per_plate_inr": COST_PER_PLATE_INR,
        "overflow_cost_inr": overflow * COST_PER_PLATE_INR,
        "buffer_breached": overflow > 0,
    }


def csv_report() -> str:
    """One row per household plus a total. Pending households count as everyone invited."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["household", "segment", "status", "invited", "plus_ones", "plates", "diet"])
    for h in db.list_households():
        if h["status"] == "pending":
            plus_ones, plates, diet = 0, h["invited_count"], "not known yet"
        else:
            plus_ones, plates, diet = h["plus_ones"], h["headcount"] + h["plus_ones"], h["diet"]
        writer.writerow(
            [h["name"], h["segment"], h["status"], h["invited_count"], plus_ones, plates, diet]
        )
    total = impact()
    writer.writerow(
        ["TOTAL", "", "", total["invited_plates"], total["confirmed_plus_ones"], total["predicted_plates"], ""]
    )
    return out.getvalue()
