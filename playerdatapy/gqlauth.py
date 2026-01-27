"""
GraphQL client for the Playerdata API
"""

from enum import Enum
from requests_oauthlib import OAuth2Session  # type: ignore[import-untyped]
from oauthlib.oauth2 import TokenExpiredError  # type: ignore[import-untyped]

from playerdatapy.auth.authorisation_code_flow import AuthorisationCodeFlow
from playerdatapy.auth.authorisation_code_flow_pcke import AuthorisationCodeFlowPCKE
from playerdatapy.auth.client_credentials_flow import ClientCredentialsFlow
from playerdatapy.constants import API_BASE_URL


class AuthenticationType(Enum):
    AUTHORISATION_CODE_FLOW = "authorisation_code_flow"
    AUTHORISATION_CODE_FLOW_PCKE = "authorisation_code_flow_pcke"
    CLIENT_CREDENTIALS_FLOW = "client_credentials_flow"


class GraphqlAuth:
    """
    Interface for the Playerdata graphql api
    """

    def __init__(
        self,
        client_id: str,
        token_file: str = ".token",
        client_secret: str = "",
        redirect_uri: str = "http://localhost:8888",
        port: int = 8888,
        type: AuthenticationType = AuthenticationType.AUTHORISATION_CODE_FLOW,
    ):
        self.client_id = client_id
        self.token_file = token_file
        self.authenticator = None
        self.authentication_type = type
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.port = port
        self.authenticated_session = self._get_authenticated_session()

    def _get_authenticated_session(self):
        match self.authentication_type:
            case AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE:
                self.authenticator = AuthorisationCodeFlowPCKE(
                    self.client_id, self.port, self.token_file
                )
            case AuthenticationType.AUTHORISATION_CODE_FLOW:
                self.authenticator = AuthorisationCodeFlow(
                    self.client_id, self.port, self.client_secret, self.token_file
                )
            case AuthenticationType.CLIENT_CREDENTIALS_FLOW:
                self.authenticator = ClientCredentialsFlow(
                    self.client_id, self.client_secret, self.token_file
                )

        try:
            token = self.authenticator.get_token()
        except TokenExpiredError:
            self.authenticator.authenticate(self.redirect_uri)
            token = self.authenticator.get_token()

        return OAuth2Session(
            self.client_id,
            token=token,
            auto_refresh_url=f"{API_BASE_URL}/oauth/token",
            token_updater=self.authenticator.save_token,
        )

    def _get_authentication_token(self):
        return self.authenticated_session.token["access_token"]
