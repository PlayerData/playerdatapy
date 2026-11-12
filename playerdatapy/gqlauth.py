"""
GraphQL client for the Playerdata API
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Union

from requests_oauthlib import OAuth2Session  # type: ignore[import-untyped]
from oauthlib.oauth2 import TokenExpiredError  # type: ignore[import-untyped]

from playerdatapy.auth.authorisation_code_flow import AuthorisationCodeFlow
from playerdatapy.auth.authorisation_code_flow_pcke import AuthorisationCodeFlowPCKE
from playerdatapy.auth.client_credentials_flow import ClientCredentialsFlow
from playerdatapy.auth.device_authorization_flow import (
    DeviceAuthorizationFlow,
    DevicePromptHandler,
)
from playerdatapy.auth.errors import RefreshFailedError
from playerdatapy.auth.token_refresher import TokenRefresher
from playerdatapy.auth.token_storage import default_token_path
from playerdatapy.constants import API_BASE_URL, GRAPHQL_URL, graphql_url_for


class AuthenticationType(Enum):
    AUTHORISATION_CODE_FLOW = "authorisation_code_flow"
    AUTHORISATION_CODE_FLOW_PCKE = "authorisation_code_flow_pcke"
    CLIENT_CREDENTIALS_FLOW = "client_credentials_flow"
    DEVICE_FLOW = "device_flow"


class GraphqlAuth:
    """
    Interface for the Playerdata graphql api
    """

    def __init__(
        self,
        client_id: str,
        token_file: Optional[Union[str, Path]] = None,
        client_secret: str = "",
        redirect_uri: str = "http://localhost:8888",
        port: int = 8888,
        type: AuthenticationType = AuthenticationType.AUTHORISATION_CODE_FLOW,
        base_url: Optional[str] = None,
        device_prompt: Optional[DevicePromptHandler] = None,
    ):
        self.client_id = client_id
        self.token_file: Path = Path(token_file) if token_file else default_token_path()
        self.authenticator = None
        self.authentication_type = type
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.port = port
        self.api_base_url = base_url or API_BASE_URL
        self.graphql_url = graphql_url_for(base_url) if base_url else GRAPHQL_URL
        self.device_prompt = device_prompt
        self.authenticated_session: Optional[OAuth2Session] = None
        self.authenticated_session = self._get_authenticated_session()

    def _build_authenticator(self):
        match self.authentication_type:
            case AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE:
                return AuthorisationCodeFlowPCKE(
                    self.client_id, self.port, self.token_file, self.api_base_url
                )
            case AuthenticationType.AUTHORISATION_CODE_FLOW:
                return AuthorisationCodeFlow(
                    self.client_id,
                    self.port,
                    self.client_secret,
                    self.token_file,
                    self.api_base_url,
                )
            case AuthenticationType.CLIENT_CREDENTIALS_FLOW:
                return ClientCredentialsFlow(
                    self.client_id,
                    self.client_secret,
                    self.token_file,
                    self.api_base_url,
                )
            case AuthenticationType.DEVICE_FLOW:
                return DeviceAuthorizationFlow(
                    self.client_id,
                    self.token_file,
                    self.api_base_url,
                    on_prompt=self.device_prompt,
                    client_secret=self.client_secret,
                )

    def _get_authenticated_session(self):
        self.authenticator = self._build_authenticator()
        token = self._load_or_login()
        self.httpx_auth = self._build_refresher(token)
        return OAuth2Session(self.client_id, token=token)

    def _load_or_login(self) -> dict:
        try:
            return self.authenticator.get_token()
        except TokenExpiredError:
            pass

        stored = self.authenticator.load_stored_token()
        if stored is not None and "refresh_token" in stored:
            try:
                return self._build_refresher(stored).ensure_fresh()
            except RefreshFailedError:
                pass

        self.authenticator.authenticate(self.redirect_uri)
        return self.authenticator.get_token()

    def _build_refresher(self, token: dict) -> TokenRefresher:
        return TokenRefresher(
            self.authenticator,
            token,
            allowed_urls=[self.api_base_url, self.graphql_url],
            on_token_updated=self._sync_session_token,
        )

    def _sync_session_token(self, token: dict) -> None:
        if self.authenticated_session is not None:
            self.authenticated_session.token = token

    def _get_authentication_token(self):
        return self.authenticated_session.token["access_token"]
