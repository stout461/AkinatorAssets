import os

from dotenv import load_dotenv

load_dotenv()  # Load from .env if it exists

CLIENT_ID = os.getenv("SCHWAB_CLIENT_ID", "fallback-from-config")
CLIENT_SECRET = os.getenv("SCHWAB_CLIENT_SECRET", "fallback-from-config")
REFRESH_TOKEN = os.getenv("SCHWAB_REFRESH_TOKEN", "fallback-from-config")
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
