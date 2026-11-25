"""Voice RSVP pipeline: audio in, saved RSVP and a spoken reply out."""
from pathlib import Path

from app import replies, rsvp, sarvam

MIN_CONFIDENCE = 0.5  # below this we ask again instead of guessing a headcount
MAX_AUDIO_BYTES = 10 * 1024 * 1024
SAMPLES_DIR = Path(__file__).parent.parent / "samples"
SAMPLE_TYPES = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".webm", ".aac"}


def submit(audio: bytes, filename: str, household_id: int, channel: str) -> dict:
    household = rsvp.find_household(household_id)  # before spending any Sarvam credits
    if rsvp.household_flags(household)["voice_fallback_text"]["enabled"]:
        raise rsvp.RsvpRejected(
            503, "voice_disabled", "Please use the form for your RSVP.", fallback="text"
        )
    if len(audio) > MAX_AUDIO_BYTES:
        raise rsvp.RsvpRejected(413, "audio_too_large", "That recording is too large.")

    heard = sarvam.transcribe(audio, filename)
    if not heard["transcript"]:
        raise rsvp.RsvpRejected(422, "no_speech", "We could not hear anything. Please try again.")
    parsed = sarvam.extract_rsvp(heard["transcript"], household)

    understood = {
        "transcript": heard["transcript"],
        "detected_language": heard["language"],
        "parsed": parsed.model_dump(),
    }
    # Near-silence is often heard as a single word such as "yes". That is not a headcount.
    words = heard["transcript"].split()
    too_short = len(words) < 2 and not any(c.isdigit() for c in heard["transcript"])
    try:
        if parsed.confidence < MIN_CONFIDENCE or (parsed.attending and too_short):
            raise rsvp.RsvpRejected(
                422, "not_understood", "Please say how many of you are coming, and veg or non-veg."
            )
        saved = rsvp.submit(household_id, parsed, channel, heard["transcript"])
    except rsvp.RsvpRejected as exc:
        exc.extra |= understood  # so the guest sees what we heard, even on a rejection
        raise

    return {
        **understood,
        "rsvp": saved,
        "reply_text": replies.confirmation(household["language"], saved),
        "reply_audio_url": f"/api/rsvp/{saved['id']}/reply-audio",
    }


def list_samples() -> list[str]:
    return sorted(p.stem for p in SAMPLES_DIR.glob("*") if p.suffix.lower() in SAMPLE_TYPES)


def load_sample(name: str) -> tuple[bytes, str]:
    # Compare against a directory listing, so the name from the URL is never used as a path.
    for path in SAMPLES_DIR.glob("*"):
        if path.stem == name and path.suffix.lower() in SAMPLE_TYPES:
            return path.read_bytes(), path.name
    raise rsvp.RsvpRejected(404, "sample_not_found", f"No sample '{name}'. See samples/README.md.")
