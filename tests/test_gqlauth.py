from unittest.mock import MagicMock, patch

import pytest
from oauthlib.oauth2 import TokenExpiredError  # type: ignore[import-untyped]

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
        assert auth.token_file == ".token"
        assert auth.redirect_uri == "http://localhost:8888"
        assert auth.port == 8888
        assert auth.authentication_type == AuthenticationType.CLIENT_CREDENTIALS_FLOW
        assert auth.authenticator == mock_authenticator
        mock_flow_class.assert_called_once_with("test_client", "test_secret", ".token")

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
        assert auth.token_file == ".test_token"
        assert auth.redirect_uri == "http://localhost:9999"
        assert auth.port == 9999
        assert auth.authentication_type == AuthenticationType.AUTHORISATION_CODE_FLOW
        mock_flow_class.assert_called_once_with(
            "test_client", 9999, "test_secret", ".test_token"
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
        mock_flow_class.assert_called_once_with("test_client", 8888, ".test_token")

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
            "test_client",
            token={"access_token": "test_token"},
            auto_refresh_url="https://app.playerdata.co.uk/oauth/token",
            token_updater=mock_authenticator.save_token,
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
