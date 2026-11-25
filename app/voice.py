"""Conversational RSVPs: a voice note or a chat message in, a saved RSVP and a reply out."""
import time
from pathlib import Path

from app import replies, rsvp, sarvam

MIN_CONFIDENCE = 0.5  # below this we ask again instead of guessing a headcount
MAX_AUDIO_BYTES = 10 * 1024 * 1024
SAMPLES_DIR = Path(__file__).parent.parent / "samples"
SAMPLE_TYPES = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".webm", ".aac"}


def submit(audio: bytes, filename: str, household_id: int, channel: str) -> dict:
    household = rsvp.find_household(household_id)  # before spending any Sarvam credits
    state = rsvp.household_flags(household)
    if state["voice_fallback_text"]["enabled"]:
        raise rsvp.RsvpRejected(
            503, "voice_disabled", "Please use the form for your RSVP.", fallback="text"
        )
    if len(audio) > MAX_AUDIO_BYTES:
        raise rsvp.RsvpRejected(413, "audio_too_large", "That recording is too large.")

    start = time.perf_counter()
    heard = sarvam.transcribe(audio, filename)
    stt_ms = round((time.perf_counter() - start) * 1000)
    if not heard["transcript"]:
        raise rsvp.RsvpRejected(422, "no_speech", "We could not hear anything. Please try again.")
    return _answer(household, state, heard, channel, {"stt": stt_ms})


def submit_message(text: str, household_id: int) -> dict:
    """The same steps for a typed chat message, without speech to text."""
    household = rsvp.find_household(household_id)
    typed = {"transcript": text, "language": None, "saved": False}
    return _answer(household, rsvp.household_flags(household), typed, "web_text", {})


def _answer(household: dict, state: dict, heard: dict, channel: str, timings: dict) -> dict:
    text = heard["transcript"]
    start = time.perf_counter()
    parsed = sarvam.extract_rsvp(text, household)
    timings["llm"] = round((time.perf_counter() - start) * 1000)
    understood = {
        "transcript": text,
        "detected_language": heard["language"],
        "saved_transcript": heard["saved"],  # true if Sarvam failed and we reused an earlier one
        "parsed": parsed.model_dump(),
        "rules": {
            "segment": household["segment"],
            "allow_plus_ones": state["allow_plus_ones"]["enabled"],
            "catering_locked": state["catering_lock_mode"]["enabled"],
        },
        "timings_ms": timings,
    }
    # Near-silence is often heard as a single word such as "yes". That is not a headcount.
    too_short = len(text.split()) < 2 and not any(c.isdigit() for c in text)
    try:
        if parsed.confidence < MIN_CONFIDENCE or (parsed.attending and too_short):
            raise rsvp.RsvpRejected(
                422, "not_understood", "Please say how many of you are coming, and veg or non-veg."
            )
        saved = rsvp.submit(household["id"], parsed, channel, text, state)
    except rsvp.RsvpRejected as exc:
        exc.extra |= understood  # so the guest sees what we heard, even on a rejection
        if exc.code in replies.REFUSALS:
            exc.extra["reply_text"] = replies.refusal(household, exc.code)
            exc.extra["reply_audio_url"] = f"/api/households/{household['id']}/refusal-audio/{exc.code}"
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
