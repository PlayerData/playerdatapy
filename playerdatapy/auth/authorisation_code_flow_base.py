import webbrowser
from requests_oauthlib import OAuth2Session

from .base_flow import BaseAuthFlow
from .server import Server


class AuthorisationCodeFlowBase(BaseAuthFlow):
    """Base class for OAuth2 authorization code flows with token management."""

    def __init__(self, client_id: str, port: int, token_file: str = ".token"):
        super().__init__(client_id, token_file)
        self.server = Server(port)

    def authenticate(self, redirect_uri):
        print("Logging you into the GraphQL API")

        self.oauth_session = OAuth2Session(self.client_id, redirect_uri=redirect_uri)

        self.server.start()

        try:
            authorization_url, _ = self.oauth_session.authorization_url(
                f"{self.api_base_url}/oauth/authorize"
            )

            self._open_browser_for_authorization(authorization_url)
            code = self.server.wait_for_callback()
            token = self._fetch_token(code)
            self.save_token(token)

            print("Login successful, token saved to file!")
            return token

        finally:
            if self.server:
                self.server.stop()

    def _open_browser_for_authorization(self, authorization_url: str):
        """Open browser for authorization and print instructions."""
        webbrowser.open(authorization_url)
        print(
            f"If your browser does not open automatically please go to the following link: {authorization_url}"
        )

    def _fetch_token(self, code: str) -> dict:
        """Exchange authorization code for access token. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _fetch_token")
