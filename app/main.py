from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import catering, db, flags, rsvp, seed
from app.config import CATERER_BUFFER_PLATES, SARVAM_API_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed.seed()  # creates the tables and guest list on first run
    yield


app = FastAPI(title="ShaadiCount", lifespan=lifespan)


@app.exception_handler(rsvp.RsvpRejected)
def rsvp_rejected(request: Request, exc: rsvp.RsvpRejected):
    return JSONResponse(status_code=exc.status, content={"error": exc.code, "message": exc.message})


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return {
        "sarvam_configured": bool(SARVAM_API_KEY),
        "allow_plus_ones": flags.is_enabled("allow_plus_ones", default=True),
        "flagsmith_last_error": flags.last_error,
        "caterer_buffer_plates": CATERER_BUFFER_PLATES,
    }


@app.get("/api/households")
def households():
    return db.list_households()


class TextRsvp(rsvp.Rsvp):
    household_id: int


@app.post("/api/rsvp/text")
def rsvp_text(body: TextRsvp):
    return rsvp.submit(body.household_id, body, channel="web_text")


@app.get("/api/catering/impact")
def catering_impact():
    return catering.impact()


@app.post("/api/demo/reset")
def demo_reset():
    seed.reset()
    return {"status": "reset", "impact": catering.impact()}
