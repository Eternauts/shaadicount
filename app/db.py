"""SQLite storage: one file, two tables, one short-lived connection per call."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "shaadicount.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS households (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    phone         TEXT,
    segment       TEXT NOT NULL CHECK (segment IN ('close_family', 'relatives', 'colleagues')),
    invited_count INTEGER NOT NULL CHECK (invited_count > 0),
    language      TEXT NOT NULL CHECK (language IN ('hi-IN', 'kn-IN', 'ta-IN', 'en-IN'))
);
CREATE TABLE IF NOT EXISTS rsvps (
    id           INTEGER PRIMARY KEY,
    household_id INTEGER NOT NULL REFERENCES households(id),
    attending    INTEGER NOT NULL CHECK (attending IN (0, 1)),
    headcount    INTEGER NOT NULL CHECK (headcount >= 0),
    plus_ones    INTEGER NOT NULL CHECK (plus_ones >= 0),
    diet         TEXT NOT NULL CHECK (diet IN ('veg', 'non_veg', 'jain', 'mixed')),
    channel      TEXT NOT NULL CHECK (channel IN ('web_voice', 'web_text', 'whatsapp')),
    transcript   TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS rsvps_by_household ON rsvps (household_id);
"""


@contextmanager
def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:  # commits on success, rolls back on an exception
            yield conn
    finally:
        conn.close()


def init() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def list_households() -> list[dict]:
    """Every household with its latest RSVP. RSVPs are append-only, so the newest one counts."""
    # phone is left out on purpose: this feeds an unauthenticated endpoint.
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT h.id, h.name, h.segment, h.invited_count, h.language,
                   r.id AS rsvp_id, r.attending, r.headcount, r.plus_ones,
                   r.diet, r.channel, r.created_at
            FROM households h
            LEFT JOIN rsvps r
                   ON r.id = (SELECT MAX(id) FROM rsvps WHERE household_id = h.id)
            ORDER BY h.id
            """
        ).fetchall()
    households = []
    for row in rows:
        household = dict(row)
        if household["rsvp_id"] is None:
            household["status"] = "pending"
        else:
            household["attending"] = bool(household["attending"])
            household["status"] = "confirmed" if household["attending"] else "declined"
        households.append(household)
    return households


def get_household(household_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM households WHERE id = ?", (household_id,)).fetchone()
    return dict(row) if row else None


def save_rsvp(
    household_id: int,
    attending: bool,
    headcount: int,
    plus_ones: int,
    diet: str,
    channel: str,
    transcript: str | None = None,
) -> dict:
    rsvp = {
        "household_id": household_id,
        "attending": attending,
        "headcount": headcount,
        "plus_ones": plus_ones,
        "diet": diet,
        "channel": channel,
        "transcript": transcript,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO rsvps (household_id, attending, headcount, plus_ones,
                               diet, channel, transcript, created_at)
            VALUES (:household_id, :attending, :headcount, :plus_ones,
                    :diet, :channel, :transcript, :created_at)
            """,
            rsvp,
        )
    return {"id": cursor.lastrowid, **rsvp}


def get_rsvp(rsvp_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM rsvps WHERE id = ?", (rsvp_id,)).fetchone()
    return dict(row) if row else None
