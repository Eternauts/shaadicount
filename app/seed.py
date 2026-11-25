"""Demo guest list. Run with: python -m app.seed"""
from app import db

# Fixed ids keep invite links such as /invite/1 stable across resets.
# (id, name, segment, invited_count, language). Phones stay empty until WhatsApp needs one.
HOUSEHOLDS = [
    (1, "Sharma Parivar, Delhi", "close_family", 6, "hi-IN"),
    (2, "Iyer Family, Chennai", "close_family", 8, "ta-IN"),
    (3, "Gowda Kutumba, Mysuru", "close_family", 10, "kn-IN"),
    (4, "Agarwal Khandaan, Jaipur", "close_family", 56, "hi-IN"),
    (5, "Reddy Family, Hyderabad", "close_family", 50, "en-IN"),
    (6, "Verma Family, Lucknow", "relatives", 48, "hi-IN"),
    (7, "Hegde Family, Sirsi", "relatives", 42, "kn-IN"),
    (8, "Subramanian Family, Madurai", "relatives", 40, "ta-IN"),
    (9, "Khanna Family, Amritsar", "relatives", 40, "hi-IN"),
    (10, "Mehta and Finance Team", "colleagues", 35, "en-IN"),
    (11, "D'Souza and Design Team", "colleagues", 30, "en-IN"),
    (12, "Rao and Platform Team", "colleagues", 25, "kn-IN"),
]


def seed() -> None:
    """Idempotent: adds any missing household, leaves existing rows and RSVPs alone."""
    db.init()
    with db.connect() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO households (id, name, segment, invited_count, language)
            VALUES (?, ?, ?, ?, ?)
            """,
            HOUSEHOLDS,
        )


def reset() -> None:
    """Back to the starting state: the full guest list, no RSVPs."""
    db.init()
    with db.connect() as conn:
        conn.execute("DELETE FROM rsvps")
        conn.execute("DELETE FROM households")
    seed()


if __name__ == "__main__":
    seed()
    print(f"{len(db.list_households())} households in {db.DB_PATH}")
