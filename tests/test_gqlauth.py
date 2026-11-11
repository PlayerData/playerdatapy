import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from oauthlib.oauth2 import TokenExpiredError  # type: ignore[import-untyped]

from playerdatapy.auth.device_authorization_flow import DeviceAuthorizationFlow
from playerdatapy.auth.token_storage import default_token_path
from playerdatapy.constants import API_BASE_URL
from playerdatapy.gqlauth import GraphqlAuth, AuthenticationType


class TestGraphqlAuth:
    """Tests for GraphqlAuth class."""

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    def test_init_client_credentials_flow(self, mock_flow_class, mock_session_class):
        """Test GraphqlAuth initialization with CLIENT_CREDENTIALS_FLOW."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        auth = GraphqlAuth(
            client_id="test_client",
            client_secret="test_secret",
            type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
        )

        assert auth.client_id == "test_client"
        assert auth.client_secret == "test_secret"
        assert auth.token_file == default_token_path()
        assert auth.redirect_uri == "http://localhost:8888"
        assert auth.port == 8888
        assert auth.authentication_type == AuthenticationType.CLIENT_CREDENTIALS_FLOW
        assert auth.authenticator == mock_authenticator
        mock_flow_class.assert_called_once_with(
            "test_client", "test_secret", default_token_path(), API_BASE_URL
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.DeviceAuthorizationFlow")
    def test_init_device_flow(self, mock_flow_class, mock_session_class):
        """Test GraphqlAuth initialization with DEVICE_FLOW."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        auth = GraphqlAuth(
            client_id="test_client",
            type=AuthenticationType.DEVICE_FLOW,
        )

        assert auth.authentication_type == AuthenticationType.DEVICE_FLOW
        assert auth.authenticator == mock_authenticator
        mock_flow_class.assert_called_once_with(
            "test_client",
            default_token_path(),
            API_BASE_URL,
            on_prompt=None,
            client_secret="",
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.DeviceAuthorizationFlow")
    def test_init_device_flow_with_client_secret(
        self, mock_flow_class, mock_session_class
    ):
        """Test GraphqlAuth passes client_secret through to DEVICE_FLOW."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        GraphqlAuth(
            client_id="test_client",
            client_secret="test_secret",
            type=AuthenticationType.DEVICE_FLOW,
        )

        mock_flow_class.assert_called_once_with(
            "test_client",
            default_token_path(),
            API_BASE_URL,
            on_prompt=None,
            client_secret="test_secret",
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlow")
    def test_init_authorisation_code_flow(self, mock_flow_class, mock_session_class):
        """Test GraphqlAuth initialization with AUTHORISATION_CODE_FLOW."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        auth = GraphqlAuth(
            client_id="test_client",
            client_secret="test_secret",
            port=9999,
            redirect_uri="http://localhost:9999",
            token_file=".test_token",
            type=AuthenticationType.AUTHORISATION_CODE_FLOW,
        )

        assert auth.client_id == "test_client"
        assert auth.client_secret == "test_secret"
        assert auth.token_file == Path(".test_token")
        assert auth.redirect_uri == "http://localhost:9999"
        assert auth.port == 9999
        assert auth.authentication_type == AuthenticationType.AUTHORISATION_CODE_FLOW
        mock_flow_class.assert_called_once_with(
            "test_client", 9999, "test_secret", Path(".test_token"), API_BASE_URL
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlowPCKE")
    def test_init_authorisation_code_flow_pcke(
        self, mock_flow_class, mock_session_class
    ):
        """Test GraphqlAuth initialization with AUTHORISATION_CODE_FLOW_PCKE."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        auth = GraphqlAuth(
            client_id="test_client",
            port=8888,
            token_file=".test_token",
            type=AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE,
        )

        assert (
            auth.authentication_type == AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE
        )
        mock_flow_class.assert_called_once_with(
            "test_client", 8888, Path(".test_token"), API_BASE_URL
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    def test_init_with_base_url(self, mock_flow_class, mock_session_class):
        """Test base_url overrides the default and reaches the flow."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        auth = GraphqlAuth(
            client_id="test_client",
            client_secret="test_secret",
            type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
            base_url="https://preview.playerdata.co.uk",
        )

        assert auth.api_base_url == "https://preview.playerdata.co.uk"
        mock_flow_class.assert_called_once_with(
            "test_client",
            "test_secret",
            default_token_path(),
            "https://preview.playerdata.co.uk",
        )
        mock_session_class.assert_called_once_with(
            "test_client", token={"access_token": "test_token"}
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    def test_get_authenticated_session_with_valid_token(
        self, mock_flow_class, mock_session_class
    ):
        """Test _get_authenticated_session with valid token."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        GraphqlAuth(
            client_id="test_client",
            client_secret="test_secret",
            type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
        )

        mock_authenticator.get_token.assert_called_once()
        mock_session_class.assert_called_once_with(
            "test_client", token={"access_token": "test_token"}
        )

    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    def test_get_authenticated_session_with_expired_token(
        self, mock_flow_class, mock_session_class
    ):
        """Test _get_authenticated_session with expired token triggers re-authentication."""
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.side_effect = [
            TokenExpiredError("Token expired"),
            {"access_token": "new_token"},
        ]
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "new_token"}
        mock_session_class.return_value = mock_session

        GraphqlAuth(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8888",
            type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
        )

        # Should call get_token twice: once initially (expired), then after authenticate
        assert mock_authenticator.get_token.call_count == 2
        mock_authenticator.authenticate.assert_called_once_with("http://localhost:8888")

    def test_get_authentication_token(self):
        """Test _get_authentication_token returns access token."""
        auth = GraphqlAuth.__new__(GraphqlAuth)
        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_access_token"}
        auth.authenticated_session = mock_session

        token = auth._get_authentication_token()
        assert token == "test_access_token"

    def test_get_authentication_token_missing_access_token(self):
        """Test _get_authentication_token raises error when access_token is missing."""
        auth = GraphqlAuth.__new__(GraphqlAuth)
        mock_session = MagicMock()
        mock_session.token = {"token_type": "Bearer"}
        auth.authenticated_session = mock_session

        with pytest.raises(KeyError):
            auth._get_authentication_token()


def _write_token(token_file, access, refresh="old-refresh", expires_in=-60):
    token = {
        "access_token": access,
        "token_type": "Bearer",
        "expires_at": time.time() + expires_in,
    }
    if refresh is not None:
        token["refresh_token"] = refresh
    token_file.write_text(json.dumps(token))


def _token_endpoint(response, calls):
    def handler(request):
        if request.url.path == "/oauth/token":
            calls.append(request)
            return response
        return httpx.Response(200, json={"data": {}})

    return handler


def _refreshed():
    return httpx.Response(
        200,
        json={
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "token_type": "Bearer",
            "expires_in": 7200,
        },
    )


class TestGraphqlAuthRefresh:
    """Startup and on-demand refresh through the saved refresh token."""

    def _auth(self, token_file):
        return GraphqlAuth(
            client_id="test_client",
            token_file=token_file,
            type=AuthenticationType.DEVICE_FLOW,
        )

    def _auth_via(self, mock_httpx, token_file, handler):
        mock_httpx(handler)
        return self._auth(token_file)

    @patch.object(DeviceAuthorizationFlow, "authenticate")
    def test_expired_token_refreshes_without_login(
        self, mock_authenticate, tmp_path, mock_httpx
    ):
        token_file = tmp_path / "token.json"
        _write_token(token_file, "old-access")
        calls = []

        auth = self._auth_via(
            mock_httpx, token_file, _token_endpoint(_refreshed(), calls)
        )

        mock_authenticate.assert_not_called()
        assert len(calls) == 1
        assert auth.httpx_auth.token["access_token"] == "new-access"
        assert auth.authenticated_session.token["access_token"] == "new-access"
        assert json.loads(token_file.read_text())["refresh_token"] == "new-refresh"

    @patch.object(DeviceAuthorizationFlow, "authenticate")
    def test_rejected_refresh_falls_back_to_login(
        self, mock_authenticate, tmp_path, mock_httpx
    ):
        token_file = tmp_path / "token.json"
        _write_token(token_file, "old-access")
        mock_authenticate.side_effect = lambda _redirect_uri: _write_token(
            token_file, "login-access", expires_in=3600
        )
        rejected = httpx.Response(400, json={"error": "invalid_grant"})

        auth = self._auth_via(mock_httpx, token_file, _token_endpoint(rejected, []))

        mock_authenticate.assert_called_once()
        assert auth.httpx_auth.token["access_token"] == "login-access"

    @patch.object(DeviceAuthorizationFlow, "authenticate")
    def test_unavailable_refresh_propagates_without_login(
        self, mock_authenticate, tmp_path, mock_httpx
    ):
        token_file = tmp_path / "token.json"
        _write_token(token_file, "old-access")
        unavailable = httpx.Response(503, text="down")

        with pytest.raises(httpx.HTTPStatusError):
            self._auth_via(mock_httpx, token_file, _token_endpoint(unavailable, []))

        mock_authenticate.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_token_follows_mid_run_refresh(self, tmp_path):
        token_file = tmp_path / "token.json"
        _write_token(token_file, "old-access", expires_in=3600)
        auth = self._auth(token_file)

        def handler(request):
            if request.url.path == "/oauth/token":
                return _refreshed()
            if request.headers["Authorization"] == "Bearer old-access":
                return httpx.Response(401)
            return httpx.Response(200, json={"data": {}})

        async with httpx.AsyncClient(
            auth=auth.httpx_auth, transport=httpx.MockTransport(handler)
        ) as client:
            await client.post(f"{API_BASE_URL}/api/graphql")

        assert auth.authenticated_session.token["access_token"] == "new-access"
