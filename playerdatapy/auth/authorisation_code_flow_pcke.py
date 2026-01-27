from .authorisation_code_flow_base import AuthorisationCodeFlowBase


class AuthorisationCodeFlowPCKE(AuthorisationCodeFlowBase):
    """Handles oauth2 authentication code flow with PKCE and token management."""

    def _fetch_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        return self.oauth_session.fetch_token(
            f"{self.api_base_url}/oauth/token",
            code=code,
        )
