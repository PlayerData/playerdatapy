from unittest.mock import MagicMock, patch


from playerdatapy.auth.authorisation_code_flow import AuthorisationCodeFlow


class TestAuthorisationCodeFlow:
    """Tests for AuthorisationCodeFlow class."""

    def test_init(self):
        """Test AuthorisationCodeFlow initialization."""
        with patch(
            "playerdatapy.auth.authorisation_code_flow_base.Server"
        ) as mock_server_class:
            mock_server = MagicMock()
            mock_server_class.return_value = mock_server

            flow = AuthorisationCodeFlow(
                client_id="test_client",
                port=8080,
                client_secret="test_secret",
                token_file=".test_token",
            )

            assert flow.client_id == "test_client"
            assert flow.client_secret == "test_secret"
            assert flow.token_file == ".test_token"
            assert flow.server == mock_server

    def test_fetch_token_with_client_secret(self):
        """Test _fetch_token includes client_secret."""
        with patch("playerdatapy.auth.authorisation_code_flow_base.Server"):
            flow = AuthorisationCodeFlow(
                client_id="test_client",
                port=8080,
                client_secret="test_secret",
            )

            mock_session = MagicMock()
            mock_session.fetch_token.return_value = {"access_token": "test_token"}
            flow.oauth_session = mock_session

            result = flow._fetch_token("test_code")

            mock_session.fetch_token.assert_called_once_with(
                "https://app.playerdata.co.uk/oauth/token",
                code="test_code",
                client_secret="test_secret",
            )
            assert result == {"access_token": "test_token"}
