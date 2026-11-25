import logging
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

from app import catering, db, flags, replies, rsvp, sarvam, seed, voice
from app.config import CATERER_BUFFER_PLATES, SARVAM_API_KEY

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # it would log every outgoing URL

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed.seed()  # creates the tables and guest list on first run
    yield


app = FastAPI(title="ShaadiCount", lifespan=lifespan)


@app.exception_handler(rsvp.RsvpRejected)
def rsvp_rejected(request: Request, exc: rsvp.RsvpRejected):
    content = {"error": exc.code, "message": exc.message, **exc.extra}
    return JSONResponse(status_code=exc.status, content=content)


@app.exception_handler(sarvam.SarvamError)
def sarvam_failed(request: Request, exc: sarvam.SarvamError):
    return JSONResponse(
        status_code=502,
        content={
            "error": f"voice_{exc.step}_failed",
            "message": "Voice is not available right now. Please use the form.",
            "detail": exc.message,
            "fallback": "text",
        },
    )


@app.exception_handler(flags.FlagUpdateError)
def flag_update_failed(request: Request, exc: flags.FlagUpdateError):
    return JSONResponse(
        status_code=502, content={"error": "flag_update_failed", "message": str(exc)}
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return {
        "sarvam_configured": bool(SARVAM_API_KEY),
        "allow_plus_ones": flags.get_environment_flags()["allow_plus_ones"]["enabled"],
        "flagsmith_last_error": flags.last_error,
        "caterer_buffer_plates": CATERER_BUFFER_PLATES,
    }


@app.get("/api/flags")
def flag_state(household_id: int | None = None):
    """All four flags: the environment defaults, or what one household gets."""
    if household_id is None:
        state = flags.get_environment_flags()
    else:
        state = rsvp.household_flags(rsvp.find_household(household_id))
    # live is false when Flagsmith did not answer and these are the last known values.
    return {"flags": state, "live": flags.last_error is None, "error": flags.last_error}


@app.get("/")
def dashboard_page():
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/invite/{household_id}")
def invite_page(household_id: int):
    return FileResponse(STATIC_DIR / "invite.html")


@app.get("/api/invite/{household_id}")
def invite(household_id: int):
    """Everything the guest page needs, after Flagsmith has decided for this household."""
    household = rsvp.find_household(household_id)
    state = rsvp.household_flags(household)
    locked = state["catering_lock_mode"]["enabled"]
    latest = next(h for h in db.list_households() if h["id"] == household_id)
    answered = latest["status"] != "pending"
    return {
        "household": {k: household[k] for k in ("id", "name", "invited_count", "language")},
        "plus_ones_allowed": state["allow_plus_ones"]["enabled"] and not locked,
        "catering_locked": locked,
        "voice_enabled": not state["voice_fallback_text"]["enabled"],
        "prompt_variant": flags.get_value("rsvp_prompt_variant", state),
        "latest_rsvp": (
            {k: latest[k] for k in ("attending", "headcount", "plus_ones", "diet")} if answered else None
        ),
    }


@app.get("/api/households")
def households():
    return db.list_households()


class TextRsvp(rsvp.Rsvp):
    household_id: int


@app.post("/api/rsvp/text")
def rsvp_text(body: TextRsvp):
    return rsvp.submit(body.household_id, body, channel="web_text")


@app.post("/api/rsvp/voice")
def rsvp_voice(audio: UploadFile = File(), household_id: int = Form()):
    # Read one byte past the limit: enough to reject a huge upload without loading it all.
    data = audio.file.read(voice.MAX_AUDIO_BYTES + 1)
    return voice.submit(data, audio.filename or "", household_id, channel="web_voice")


@app.post("/api/rsvp/voice/sample/{name}")
def rsvp_voice_sample(name: str, household_id: int = 1):
    data, filename = voice.load_sample(name)
    return voice.submit(data, filename, household_id, channel="web_voice")


@app.get("/api/samples")
def samples():
    return voice.list_samples()


@app.get("/api/samples/{name}")
def sample_audio(name: str):
    data, filename = voice.load_sample(name)
    return Response(data, media_type=mimetypes.guess_type(filename)[0] or "audio/mpeg")


@app.get("/api/rsvp/{rsvp_id}/reply-audio")
def reply_audio(rsvp_id: int):
    saved = db.get_rsvp(rsvp_id)
    if saved is None:
        raise rsvp.RsvpRejected(404, "rsvp_not_found", f"No RSVP with id {rsvp_id}.")
    language = rsvp.find_household(saved["household_id"])["language"]
    audio = sarvam.speak(replies.confirmation(language, saved), language)
    # no-store: RSVP ids start again after a demo reset, so a cached reply could be wrong.
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})


@app.get("/api/catering/impact")
def catering_impact():
    return catering.impact()


@app.get("/api/caterer.csv")
def caterer_csv():
    return Response(
        catering.csv_report(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="shaadicount-caterer.csv"'},
    )


@app.post("/api/demo/reset")
def demo_reset():
    seed.reset()
    return {"status": "reset", "impact": catering.impact()}
