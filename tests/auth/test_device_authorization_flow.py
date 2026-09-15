import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from playerdatapy.auth.device_authorization_flow import (
    DeviceAuthorization,
    DeviceAuthorizationError,
    DeviceAuthorizationFlow,
)

DEVICE_CODE_RESPONSE = {
    "device_code": "device-code-123",
    "user_code": "ABCD1234",
    "verification_uri": "https://app.playerdata.co.uk/oauth/device",
    "verification_uri_complete": "https://app.playerdata.co.uk/oauth/device?user_code=ABCD1234",
    "expires_in": 300,
    "interval": 5,
}


def _response(json_data, is_success=True):
    response = MagicMock()
    response.is_success = is_success
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


class TestDeviceAuthorizationFlow:
    """Tests for DeviceAuthorizationFlow class."""

    def test_init(self):
        flow = DeviceAuthorizationFlow(
            client_id="test_client", token_file=".test_token"
        )
        assert flow.client_id == "test_client"
        assert flow.token_file == Path(".test_token")
        assert flow.scope == "public"
        assert flow.oauth_session is None

    @patch("playerdatapy.auth.device_authorization_flow.time.sleep")
    @patch("playerdatapy.auth.device_authorization_flow.httpx.post")
    def test_authenticate_requests_polls_and_saves(self, mock_post, _mock_sleep):
        token_response = {
            "access_token": "the-token",
            "token_type": "Bearer",
            "expires_in": 7200,
            "refresh_token": "the-refresh-token",
        }
        mock_post.side_effect = [
            _response(DEVICE_CODE_RESPONSE),
            _response(token_response),
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name

        try:
            flow = DeviceAuthorizationFlow(
                client_id="test_client", token_file=token_file
            )
            result = flow.authenticate()

            # 1. device authorization request
            assert (
                mock_post.call_args_list[0].args[0].endswith("/oauth/authorize_device")
            )
            assert mock_post.call_args_list[0].kwargs["data"] == {
                "client_id": "test_client",
                "scope": "public",
            }
            # 2. device_code token poll
            assert mock_post.call_args_list[1].args[0].endswith("/oauth/token")
            assert mock_post.call_args_list[1].kwargs["data"] == {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": "device-code-123",
                "client_id": "test_client",
            }

            # token returned with expires_at added, and persisted
            assert result["access_token"] == "the-token"
            assert "expires_at" in result
            saved = json.loads(Path(token_file).read_text())
            assert saved["access_token"] == "the-token"
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    @patch("playerdatapy.auth.device_authorization_flow.time.sleep")
    @patch("playerdatapy.auth.device_authorization_flow.httpx.post")
    def test_authenticate_polls_through_pending_and_slow_down(
        self, mock_post, _mock_sleep
    ):
        mock_post.side_effect = [
            _response(DEVICE_CODE_RESPONSE),
            _response({"error": "authorization_pending"}, is_success=False),
            _response({"error": "slow_down"}, is_success=False),
            _response({"access_token": "tok", "expires_in": 7200}),
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name

        try:
            flow = DeviceAuthorizationFlow(
                client_id="test_client", token_file=token_file
            )
            result = flow.authenticate()

            assert result["access_token"] == "tok"
            assert mock_post.call_count == 4  # device request + 3 polls
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    @patch("playerdatapy.auth.device_authorization_flow.time.sleep")
    @patch("playerdatapy.auth.device_authorization_flow.httpx.post")
    def test_authenticate_raises_on_error(self, mock_post, _mock_sleep):
        mock_post.side_effect = [
            _response(DEVICE_CODE_RESPONSE),
            _response({"error": "access_denied"}, is_success=False),
        ]

        flow = DeviceAuthorizationFlow(
            client_id="test_client", token_file=".test_token"
        )

        with pytest.raises(DeviceAuthorizationError, match="access_denied"):
            flow.authenticate()

    def test_with_expiry_adds_expires_at(self):
        token = DeviceAuthorizationFlow._with_expiry(
            {"access_token": "tok", "expires_in": 3600}
        )
        assert "expires_at" in token

        already = {"access_token": "tok", "expires_at": 123}
        assert DeviceAuthorizationFlow._with_expiry(already) == already

    @patch("playerdatapy.auth.device_authorization_flow.time.sleep")
    @patch("playerdatapy.auth.device_authorization_flow.httpx.post")
    def test_authenticate_invokes_prompt_callback(self, mock_post, _mock_sleep):
        mock_post.side_effect = [
            _response(DEVICE_CODE_RESPONSE),
            _response({"access_token": "tok", "expires_in": 7200}),
        ]
        received = []

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name

        try:
            flow = DeviceAuthorizationFlow(
                client_id="test_client",
                token_file=token_file,
                on_prompt=received.append,
            )
            flow.authenticate()

            assert len(received) == 1
            authorization = received[0]
            assert isinstance(authorization, DeviceAuthorization)
            assert authorization.user_code == "ABCD1234"
            assert (
                authorization.verification_uri
                == "https://app.playerdata.co.uk/oauth/device"
            )
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    def test_device_authorization_from_response_applies_defaults(self):
        authorization = DeviceAuthorization.from_response(
            {
                "device_code": "d",
                "user_code": "U",
                "verification_uri": "https://example.com/device",
            }
        )

        assert authorization.interval == 5
        assert authorization.expires_in == 300
        assert authorization.verification_uri_complete is None
