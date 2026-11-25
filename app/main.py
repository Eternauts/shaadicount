from fastapi import FastAPI

from app import flags
from app.config import CATERER_BUFFER_PLATES, SARVAM_API_KEY

app = FastAPI(title="ShaadiCount")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return {
        "sarvam_configured": bool(SARVAM_API_KEY),
        "allow_plus_ones": flags.is_enabled("allow_plus_ones", default=True),
        "caterer_buffer_plates": CATERER_BUFFER_PLATES,
    }
