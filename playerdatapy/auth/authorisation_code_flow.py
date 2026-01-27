from .authorisation_code_flow_base import AuthorisationCodeFlowBase

class AuthorisationCodeFlow(AuthorisationCodeFlowBase):
    """Handles oauth2 authorisation code flow and token management."""

    def __init__(
        self, client_id: str, port: int, client_secret: str, token_file: str = ".token"
    ):
        super().__init__(client_id, port, token_file)
        self.client_secret = client_secret

    def _fetch_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        return self.oauth_session.fetch_token(
            f"{self.api_base_url}/oauth/token",
            code=code,
            client_secret=self.client_secret,
        )
