from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from .base_flow import BaseAuthFlow


class ClientCredentialsFlow(BaseAuthFlow):
    """Handles oauth2 client credentials flow and token management."""

    def __init__(self, client_id: str, client_secret: str, token_file: str = ".token"):
        super().__init__(client_id, token_file)
        self.client_secret = client_secret

    def authenticate(self, save_token: bool = True) -> dict:
        client = BackendApplicationClient(client_id=self.client_id)

        self.oauth_session = OAuth2Session(
            client=client,
        )

        try:
            token = self._fetch_token()

            if save_token:
                self.save_token(token)
                print("Login successful, token saved to file!")

            return token

        finally:
            if self.oauth_session:
                self.oauth_session.close()

    def _fetch_token(self) -> dict:
        """Exchange authorization code for access token."""
        return self.oauth_session.fetch_token(
            token_url=f"{self.api_base_url}/oauth/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
