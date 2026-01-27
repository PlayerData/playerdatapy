import json
import os
import tempfile
import time

import pytest
from oauthlib.oauth2 import TokenExpiredError

from playerdatapy.auth.base_flow import BaseAuthFlow

from playerdatapy.auth.configuration import API_BASE_URL

class TestBaseAuthFlow:
    """Tests for BaseAuthFlow class."""

    def test_init(self):
        """Test BaseAuthFlow initialization."""
        flow = BaseAuthFlow(client_id="test_client", token_file=".test_token")
        assert flow.client_id == "test_client"
        assert flow.api_base_url == API_BASE_URL
        assert flow.token_file == ".test_token"
        assert flow.oauth_session is None

    def test_save_token(self):
        """Test saving token to file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name

        try:
            flow = BaseAuthFlow(client_id="test_client", token_file=token_file)
            test_token = {"access_token": "test_token", "token_type": "Bearer"}

            flow.save_token(test_token)

            # Verify token was saved
            with open(token_file, "r") as f:
                saved_data = json.loads(f.read())
                assert saved_data == test_token
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    def test_get_token_success(self):
        """Test loading token from file successfully."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name
            test_token = {"access_token": "test_token", "token_type": "Bearer"}
            f.write(json.dumps(test_token))

        try:
            flow = BaseAuthFlow(client_id="test_client", token_file=token_file)
            loaded_token = flow.get_token()
            assert loaded_token == test_token
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    def test_get_token_file_not_found(self):
        """Test get_token raises error when token file doesn't exist."""
        flow = BaseAuthFlow(client_id="test_client", token_file="nonexistent.token")
        with pytest.raises(TokenExpiredError, match="No token file found"):
            flow.get_token()

    def test_get_token_empty_file(self):
        """Test get_token raises error when token file is empty."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name
            # File is empty

        try:
            flow = BaseAuthFlow(client_id="test_client", token_file=token_file)
            with pytest.raises(TokenExpiredError, match="Token file is empty"):
                flow.get_token()
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    def test_get_token_expired(self):
        """Test get_token raises error when token is expired."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name
            # Create a token that expired 1 hour ago
            expired_token = {
                "access_token": "test_token",
                "token_type": "Bearer",
                "expires_at": time.time() - 3600,  # Expired 1 hour ago
            }
            f.write(json.dumps(expired_token))

        try:
            flow = BaseAuthFlow(client_id="test_client", token_file=token_file)
            with pytest.raises(TokenExpiredError, match="Token has expired"):
                flow.get_token()
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    def test_get_token_not_expired(self):
        """Test get_token succeeds when token is not expired."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name
            # Create a token that expires in 1 hour
            valid_token = {
                "access_token": "test_token",
                "token_type": "Bearer",
                "expires_at": time.time() + 3600,  # Expires in 1 hour
            }
            f.write(json.dumps(valid_token))

        try:
            flow = BaseAuthFlow(client_id="test_client", token_file=token_file)
            loaded_token = flow.get_token()
            assert loaded_token == valid_token
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)

    def test_get_token_no_expires_at(self):
        """Test get_token succeeds when token has no expires_at field."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
            token_file = f.name
            # Create a token without expiration info
            token_without_expiry = {
                "access_token": "test_token",
                "token_type": "Bearer",
            }
            f.write(json.dumps(token_without_expiry))

        try:
            flow = BaseAuthFlow(client_id="test_client", token_file=token_file)
            loaded_token = flow.get_token()
            assert loaded_token == token_without_expiry
        finally:
            if os.path.exists(token_file):
                os.remove(token_file)
