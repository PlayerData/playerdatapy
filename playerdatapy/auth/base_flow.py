import json
import os
import tempfile
import time
from pathlib import Path
from typing import Optional, Union

from oauthlib.oauth2 import TokenExpiredError

from playerdatapy.constants import API_BASE_URL

from .token_storage import default_token_path


class BaseAuthFlow:
    """Client settings and the saved token file shared by every OAuth flow."""

    def __init__(
        self,
        client_id: str,
        token_file: Optional[Union[str, Path]] = None,
        base_url: Optional[str] = None,
        *,
        client_secret: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = Path(token_file) if token_file else default_token_path()
        self.api_base_url = base_url or API_BASE_URL
        self.oauth_session = None

    def _client_params(self) -> dict:
        """Client credentials for a token request body."""
        params = {"client_id": self.client_id}
        if self.client_secret:
            params["client_secret"] = self.client_secret
        return params

    def load_stored_token(self) -> Optional[dict]:
        """Return the saved token, expired or not; None if missing or unreadable."""
        try:
            token = json.loads(self.token_file.read_text())
        except (FileNotFoundError, ValueError):
            return None
        return token if isinstance(token, dict) else None

    def get_token(self) -> dict:
        """Return the saved token, or raise TokenExpiredError if absent or expired."""
        token = self.load_stored_token()
        if token is None:
            raise TokenExpiredError(f"No usable token file at {self.token_file}")
        if token.get("expires_at", float("inf")) <= time.time():
            raise TokenExpiredError("Token has expired")
        return token

    def save_token(self, token: dict) -> None:
        """Write the token so a failed write leaves the old file intact.

        Refresh tokens are single-use, so a half-written file would log the user out.
        """
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.token_file.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(token, f)
            os.replace(tmp, self.token_file)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
