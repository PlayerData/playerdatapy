import json
import time
from pathlib import Path
from typing import Optional, Union
from oauthlib.oauth2 import TokenExpiredError
from playerdatapy.constants import API_BASE_URL
from .token_storage import default_token_path


class BaseAuthFlow:
    """Base class for OAuth2 authentication flows with token management."""

    def __init__(self, client_id: str, token_file: Optional[Union[str, Path]] = None):
        self.client_id = client_id
        self.token_file: Path = Path(token_file) if token_file else default_token_path()
        self.api_base_url = API_BASE_URL
        self.oauth_session = None

    def get_token(self) -> dict:
        """Load token from file and check if it's expired."""
        if not self.token_file.exists():
            raise TokenExpiredError("No token file found")

        tokens = self.token_file.read_text()
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
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(json.dumps(token))
