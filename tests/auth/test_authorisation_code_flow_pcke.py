from unittest.mock import MagicMock, patch


from playerdatapy.auth.authorisation_code_flow_pcke import AuthorisationCodeFlowPCKE


class TestAuthorisationCodeFlowPCKE:
    """Tests for AuthorisationCodeFlowPCKE class."""

    def test_init(self):
        """Test AuthorisationCodeFlowPCKE initialization."""
        with patch(
            "playerdatapy.auth.authorisation_code_flow_base.Server"
        ) as mock_server_class:
            mock_server = MagicMock()
            mock_server_class.return_value = mock_server

            flow = AuthorisationCodeFlowPCKE(
                client_id="test_client", port=8080, token_file=".test_token"
            )

            assert flow.client_id == "test_client"
            assert flow.token_file == ".test_token"
            assert flow.server == mock_server
            # Should not have client_secret attribute
            assert not hasattr(flow, "client_secret")

    def test_fetch_token_without_client_secret(self):
        """Test _fetch_token does not include client_secret (PKCE flow)."""
        with patch("playerdatapy.auth.authorisation_code_flow_base.Server"):
            flow = AuthorisationCodeFlowPCKE(
                client_id="test_client",
                port=8080,
            )

            mock_session = MagicMock()
            mock_session.fetch_token.return_value = {"access_token": "test_token"}
            flow.oauth_session = mock_session

            result = flow._fetch_token("test_code")

            # Verify client_secret is NOT passed
            mock_session.fetch_token.assert_called_once_with(
                "https://app.playerdata.co.uk/oauth/token",
                code="test_code",
            )
            # Ensure client_secret is not in the call
            call_kwargs = (
                mock_session.fetch_token.call_args[1]
                if mock_session.fetch_token.call_args[1]
                else {}
            )
            assert "client_secret" not in call_kwargs
            assert result == {"access_token": "test_token"}
