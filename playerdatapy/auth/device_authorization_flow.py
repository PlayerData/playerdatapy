import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

import httpx

from .base_flow import BaseAuthFlow

DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
DEFAULT_SCOPE = "public"
DEFAULT_POLL_INTERVAL_SECONDS = 5
DEFAULT_EXPIRES_IN_SECONDS = 300
SLOW_DOWN_INCREMENT_SECONDS = 5


class DeviceAuthorizationError(Exception):
    """Raised when the OAuth 2.0 device authorization grant cannot complete."""


@dataclass(frozen=True)
class DeviceAuthorization:
    """A device authorization response (RFC 8628 section 3.2).

    Passed to the device-flow prompt callback so the caller can surface the
    ``user_code`` and ``verification_uri`` to the end user however it likes.
    """

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    verification_uri_complete: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "DeviceAuthorization":
        return cls(
            device_code=data["device_code"],
            user_code=data["user_code"],
            verification_uri=data["verification_uri"],
            expires_in=data.get("expires_in", DEFAULT_EXPIRES_IN_SECONDS),
            interval=data.get("interval", DEFAULT_POLL_INTERVAL_SECONDS),
            verification_uri_complete=data.get("verification_uri_complete"),
        )


DevicePromptHandler = Callable[[DeviceAuthorization], None]


def default_device_prompt(authorization: DeviceAuthorization) -> None:
    """Default prompt handler: print the verification URL and user code to stdout."""
    print("To authorise this device, open:")
    print(f"  {authorization.verification_uri}")
    print(f"and enter the code: {authorization.user_code}")
    if authorization.verification_uri_complete:
        print(f"Or open this link directly: {authorization.verification_uri_complete}")


class DeviceAuthorizationFlow(BaseAuthFlow):
    """OAuth 2.0 Device Authorization Grant (RFC 8628).

    Built for headless machines with no local browser: the device requests a
    short user code, the user approves it in a browser on any device, and the
    client polls the token endpoint until a token is issued.

    ``on_prompt`` receives the :class:`DeviceAuthorization` so a caller can
    surface the code however it likes (GUI, log, etc.); it defaults to printing.
    """

    def __init__(
        self,
        client_id: str,
        token_file: Optional[Union[str, Path]] = None,
        base_url: Optional[str] = None,
        scope: str = DEFAULT_SCOPE,
        on_prompt: Optional[DevicePromptHandler] = None,
    ):
        super().__init__(client_id, token_file, base_url)
        self.scope = scope
        self._on_prompt: DevicePromptHandler = on_prompt or default_device_prompt

    def authenticate(self, redirect_uri: Optional[str] = None) -> dict:
        """Run the device flow and persist the resulting token.

        ``redirect_uri`` is accepted for parity with the other flows but is
        unused — the device grant has no redirect.
        """
        authorization = self._request_device_code()
        self._on_prompt(authorization)
        token = self._poll_for_token(authorization)

        self.save_token(token)
        print("Login successful, token saved to file!")
        return token

    def _request_device_code(self) -> DeviceAuthorization:
        response = httpx.post(
            f"{self.api_base_url}/oauth/authorize_device",
            data={"client_id": self.client_id, "scope": self.scope},
        )
        response.raise_for_status()
        return DeviceAuthorization.from_response(response.json())

    def _poll_for_token(self, authorization: DeviceAuthorization) -> dict:
        interval = authorization.interval
        deadline = time.monotonic() + authorization.expires_in

        while time.monotonic() < deadline:
            time.sleep(interval)
            response = httpx.post(
                f"{self.api_base_url}/oauth/token",
                data={
                    "grant_type": DEVICE_CODE_GRANT_TYPE,
                    "device_code": authorization.device_code,
                    "client_id": self.client_id,
                },
            )

            if response.is_success:
                return self._with_expiry(response.json())

            error = response.json().get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += SLOW_DOWN_INCREMENT_SECONDS
                continue
            raise DeviceAuthorizationError(f"Device authorisation failed: {error}")

        raise DeviceAuthorizationError("Device code expired before it was authorised.")

    @staticmethod
    def _with_expiry(token: dict) -> dict:
        """Add ``expires_at`` so expiry checks and refresh behave like the other flows."""
        if "expires_at" not in token and "expires_in" in token:
            return {**token, "expires_at": time.time() + int(token["expires_in"])}
        return token
