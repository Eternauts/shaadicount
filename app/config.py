"""All settings come from the environment (.env locally, a Secret on kind)."""
import os

from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

FLAGSMITH_CLIENT_ENVIRONMENT_KEY = os.getenv("FLAGSMITH_CLIENT_ENVIRONMENT_KEY", "")
FLAGSMITH_SERVER_ENVIRONMENT_KEY = os.getenv("FLAGSMITH_SERVER_ENVIRONMENT_KEY", "")
# Organisation API key, needed only to change flags (Phase 4). Not the same as the keys above.
FLAGSMITH_ADMIN_TOKEN = os.getenv("FLAGSMITH_ADMIN_TOKEN", "")

# "or" so that an empty value in .env still falls back to the default.
CATERER_BUFFER_PLATES = int(os.getenv("CATERER_BUFFER_PLATES") or 400)
COST_PER_PLATE_INR = int(os.getenv("COST_PER_PLATE_INR") or 1500)
