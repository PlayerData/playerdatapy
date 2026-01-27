import os
import json
import time
from oauthlib.oauth2 import TokenExpiredError
from playerdatapy.constants import API_BASE_URL


class BaseAuthFlow:
    """Base class for OAuth2 authentication flows with token management."""

    def __init__(self, client_id: str, token_file: str = ".token"):
        self.client_id = client_id
        self.token_file = token_file
        self.api_base_url = API_BASE_URL
        self.oauth_session = None

    def get_token(self) -> dict:
        """Load token from file and check if it's expired."""
        if not os.path.exists(self.token_file):
            raise TokenExpiredError("No token file found")

        with open(self.token_file, "r") as f:
            tokens = f.read()
            if not tokens:
                raise TokenExpiredError("Token file is empty")
            token = json.loads(tokens)

            if "expires_at" in token:
                current_time = time.time()
                if token["expires_at"] <= current_time:
                    raise TokenExpiredError("Token has expired")

            return token

    def save_token(self, token: dict):
        """Save token to file."""
        with open(self.token_file, "w") as f:
            f.write(json.dumps(token))
