import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
FLAGSMITH_SERVER_KEY = os.getenv("FLAGSMITH_SERVER_KEY", "")
FLAGSMITH_ADMIN_TOKEN = os.getenv("FLAGSMITH_ADMIN_TOKEN", "")
CATERER_BUFFER_PLATES = int(os.getenv("CATERER_BUFFER_PLATES", "400"))
COST_PER_PLATE_INR = int(os.getenv("COST_PER_PLATE_INR", "1500"))
