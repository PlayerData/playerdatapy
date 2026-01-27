import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from playerdatapy.auth.client_credentials_flow import ClientCredentialsFlow


class TestClientCredentialsFlow:
    """Tests for ClientCredentialsFlow class."""

    def test_init(self):
        """Test ClientCredentialsFlow initialization."""
        flow = ClientCredentialsFlow(
            client_id="test_client",
            client_secret="test_secret",
            token_file=".test_token",
        )
        assert flow.client_id == "test_client"
        assert flow.client_secret == "test_secret"
        assert flow.token_file == ".test_token"
        assert flow.oauth_session is None

    @patch("playerdatapy.auth.client_credentials_flow.OAuth2Session")
    @patch("playerdatapy.auth.client_credentials_flow.BackendApplicationClient")
    def test_authenticate_success(self, mock_client_class, mock_session_class):
        """Test successful authentication."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_session = MagicMock()
        mock_session.fetch_token.return_value = {
            "access_token": "test_token",
            "token_type": "Bearer",
        }
        mock_session_class.return_value = mock_session

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name

        try:
            flow = ClientCredentialsFlow(
                client_id="test_client",
                client_secret="test_secret",
                token_file=token_file,
            )

            result = flow.authenticate()

            # Verify OAuth2Session was created correctly
            mock_client_class.assert_called_once_with(client_id="test_client")
            mock_session_class.assert_called_once_with(client=mock_client)

            # Verify fetch_token was called
            mock_session.fetch_token.assert_called_once_with(
                token_url="https://app.playerdata.co.uk/oauth/token",
                client_id="test_client",
                client_secret="test_secret",
            )

            # Verify token was saved
            assert result == {"access_token": "test_token", "token_type": "Bearer"}
            with open(token_file, "r") as f:
                saved_token = json.loads(f.read())
                assert saved_token == {
                    "access_token": "test_token",
                    "token_type": "Bearer",
                }

            # Verify session was closed
            mock_session.close.assert_called_once()
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    @patch("playerdatapy.auth.client_credentials_flow.OAuth2Session")
    @patch("playerdatapy.auth.client_credentials_flow.BackendApplicationClient")
    def test_authenticate_closes_session_on_error(
        self, mock_client_class, mock_session_class
    ):
        """Test that session is closed even if authentication fails."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_session = MagicMock()
        mock_session.fetch_token.side_effect = Exception("Token fetch failed")
        mock_session_class.return_value = mock_session

        flow = ClientCredentialsFlow(
            client_id="test_client", client_secret="test_secret"
        )

        with pytest.raises(Exception, match="Token fetch failed"):
            flow.authenticate()

        # Verify session was still closed
        mock_session.close.assert_called_once()

    def test_fetch_token(self):
        """Test _fetch_token method."""
        flow = ClientCredentialsFlow(
            client_id="test_client", client_secret="test_secret"
        )

        mock_session = MagicMock()
        mock_session.fetch_token.return_value = {"access_token": "test_token"}
        flow.oauth_session = mock_session

        result = flow._fetch_token()

        mock_session.fetch_token.assert_called_once_with(
            token_url="https://app.playerdata.co.uk/oauth/token",
            client_id="test_client",
            client_secret="test_secret",
        )
        assert result == {"access_token": "test_token"}
