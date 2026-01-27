import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from playerdatapy.auth.authorisation_code_flow_base import AuthorisationCodeFlowBase


class TestAuthorisationCodeFlowBase:
    """Tests for AuthorisationCodeFlowBase class."""

    def test_init(self):
        """Test AuthorisationCodeFlowBase initialization."""
        with patch(
            "playerdatapy.auth.authorisation_code_flow_base.Server"
        ) as mock_server_class:
            mock_server = MagicMock()
            mock_server_class.return_value = mock_server

            flow = AuthorisationCodeFlowBase(
                client_id="test_client", port=8080, token_file=".test_token"
            )

            assert flow.client_id == "test_client"
            assert flow.token_file == ".test_token"
            assert flow.server == mock_server
            mock_server_class.assert_called_once_with(8080)

    @patch("playerdatapy.auth.authorisation_code_flow_base.webbrowser")
    @patch("playerdatapy.auth.authorisation_code_flow_base.OAuth2Session")
    @patch("playerdatapy.auth.authorisation_code_flow_base.Server")
    def test_authenticate_success(
        self, mock_server_class, mock_session_class, mock_webbrowser
    ):
        """Test successful authentication flow."""
        # Setup server mock
        mock_server = MagicMock()
        mock_server.wait_for_callback.return_value = "test_code"
        mock_server_class.return_value = mock_server

        # Setup session mock
        mock_session = MagicMock()
        mock_session.authorization_url.return_value = (
            "https://app.playerdata.co.uk/oauth/authorize?code=test",
            "state",
        )
        mock_session_class.return_value = mock_session

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name

        try:
            flow = AuthorisationCodeFlowBase(
                client_id="test_client", port=8080, token_file=token_file
            )

            # Mock _fetch_token since it's abstract
            test_token = {"access_token": "test_token", "token_type": "Bearer"}
            flow._fetch_token = MagicMock(return_value=test_token)

            result = flow.authenticate(redirect_uri="http://localhost:8080/callback")

            # Verify server was started and stopped
            mock_server.start.assert_called_once()
            mock_server.stop.assert_called_once()

            # Verify OAuth2Session was created
            mock_session_class.assert_called_once_with(
                "test_client", redirect_uri="http://localhost:8080/callback"
            )

            # Verify authorization URL was generated
            mock_session.authorization_url.assert_called_once_with(
                "https://app.playerdata.co.uk/oauth/authorize"
            )

            # Verify browser was opened
            mock_webbrowser.open.assert_called_once()

            # Verify _fetch_token was called with code
            flow._fetch_token.assert_called_once_with("test_code")

            # Verify token was saved
            assert result == test_token
            with open(token_file, "r") as f:
                saved_token = json.loads(f.read())
                assert saved_token == test_token
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    @patch("playerdatapy.auth.authorisation_code_flow_base.webbrowser")
    @patch("playerdatapy.auth.authorisation_code_flow_base.OAuth2Session")
    @patch("playerdatapy.auth.authorisation_code_flow_base.Server")
    def test_authenticate_stops_server_on_error(
        self, mock_server_class, mock_session_class, mock_webbrowser
    ):
        """Test that server is stopped even if authentication fails."""
        mock_server = MagicMock()
        mock_server.wait_for_callback.side_effect = Exception("Callback failed")
        mock_server_class.return_value = mock_server

        mock_session = MagicMock()
        mock_session.authorization_url.return_value = (
            "https://app.playerdata.co.uk/oauth/authorize?code=test",
            "state",
        )
        mock_session_class.return_value = mock_session

        flow = AuthorisationCodeFlowBase(client_id="test_client", port=8080)
        flow._fetch_token = MagicMock()

        with pytest.raises(Exception, match="Callback failed"):
            flow.authenticate(redirect_uri="http://localhost:8080/callback")

        # Verify server was still stopped
        mock_server.stop.assert_called_once()

    @patch("playerdatapy.auth.authorisation_code_flow_base.webbrowser")
    def test_open_browser_for_authorization(self, mock_webbrowser):
        """Test _open_browser_for_authorization method."""
        flow = AuthorisationCodeFlowBase(client_id="test_client", port=8080)
        authorization_url = "https://app.playerdata.co.uk/oauth/authorize?code=test"

        with patch("builtins.print") as mock_print:
            flow._open_browser_for_authorization(authorization_url)

            mock_webbrowser.open.assert_called_once_with(authorization_url)
            mock_print.assert_called_once()
            assert authorization_url in mock_print.call_args[0][0]

    def test_fetch_token_not_implemented(self):
        """Test that _fetch_token raises NotImplementedError in base class."""
        flow = AuthorisationCodeFlowBase(client_id="test_client", port=8080)

        with pytest.raises(
            NotImplementedError, match="Subclasses must implement _fetch_token"
        ):
            flow._fetch_token("test_code")
