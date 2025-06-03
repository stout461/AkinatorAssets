import requests
import time
import base64
from src.schwab_api.config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, TOKEN_URL

class SchwabAuth:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.refresh_token = REFRESH_TOKEN
        self.token_url = TOKEN_URL
        self.scope = 'readonly'
        self.access_token = None
        self.token_expiry = 0

    def _get_basic_auth_header(self):
        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(auth_str.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def refresh_access_token(self):
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'scope': self.scope
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            **self._get_basic_auth_header()
        }

        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()

        tokens = response.json()
        self.access_token = tokens['access_token']
        self.token_expiry = time.time() + tokens.get('expires_in', 1800)

    def get_access_token(self):
        if not self.access_token or time.time() > self.token_expiry:
            self.refresh_access_token()
        return self.access_token