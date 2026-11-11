import time
from typing import AsyncGenerator, Callable, Iterable, Optional

import httpx
from filelock import AsyncFileLock, FileLock
from oauthlib.oauth2 import Client, InsecureTransportError, OAuth2Error

from .base_flow import BaseAuthFlow
from .errors import RefreshFailedError

EXPIRY_MARGIN = 30
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _secure(url: httpx.URL) -> bool:
    return url.scheme == "https" or (
        url.scheme == "http" and url.host in LOOPBACK_HOSTS
    )


def _expiring(token: dict) -> bool:
    return token.get("expires_at", float("inf")) - EXPIRY_MARGIN <= time.time()


class TokenRefresher(httpx.Auth):
    """Bearer auth for `httpx.AsyncClient` that refreshes the OAuth token as needed.

    Refreshes happen one at a time across coroutines, threads and processes,
    serialised by a lock file next to the token file.
    """

    def __init__(
        self,
        flow: BaseAuthFlow,
        token: dict,
        *,
        allowed_urls: Iterable[str],
        on_token_updated: Optional[Callable[[dict], None]] = None,
        refresh_timeout: float = 15,
        lock_timeout: float = 90,
    ):
        self.flow = flow
        self.token = token
        self.on_token_updated = on_token_updated
        self.refresh_timeout = refresh_timeout
        self.lock_timeout = lock_timeout
        self._origins = {self._origin(httpx.URL(url)) for url in allowed_urls}
        self._lock_file = f"{flow.token_file}.lock"

    @staticmethod
    def _origin(url: httpx.URL) -> tuple:
        return url.scheme, url.host, url.port

    def _authorises(self, url: httpx.URL) -> bool:
        return _secure(url) and self._origin(url) in self._origins

    def _needs_refresh(self) -> bool:
        return "refresh_token" in self.token and _expiring(self.token)

    def sync_auth_flow(self, request):
        raise TypeError("TokenRefresher only works with httpx.AsyncClient")

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        if not self._authorises(request.url):
            yield request
            return
        stale = self.token if self._needs_refresh() else None
        for retry in (False, True):
            if stale is not None:
                async with AsyncFileLock(
                    self._lock_file, mode=0o600, timeout=self.lock_timeout
                ):
                    base = self._token_to_refresh(stale)
                    if base is not None:
                        response = yield self._refresh_request(base)
                        await response.aread()
                        self._finish_refresh(response, base)
            sent = self.token
            request.headers["Authorization"] = f"Bearer {sent['access_token']}"
            response = yield request
            if response.status_code != 401 or retry:
                return
            if self.token["access_token"] == sent["access_token"]:
                if "refresh_token" not in sent:
                    return
                stale = sent
            else:
                stale = None

    def ensure_fresh(self) -> dict:
        """Refresh the token now if it is about to expire, and return it."""
        if self._needs_refresh():
            stale = self.token
            with FileLock(self._lock_file, mode=0o600, timeout=self.lock_timeout):
                base = self._token_to_refresh(stale)
                if base is not None:
                    with httpx.Client() as client:
                        self._finish_refresh(
                            client.send(self._refresh_request(base)), base
                        )
        return self.token

    def _token_to_refresh(self, stale: dict) -> Optional[dict]:
        """Under the lock, adopt a token refreshed elsewhere or return the one to refresh."""
        candidates = [self.token, self.flow.load_stored_token() or {}]
        newest = max(
            (t for t in candidates if "refresh_token" in t),
            key=lambda t: t.get("expires_at", 0),
        )
        if newest.get("access_token") != stale.get("access_token") and not _expiring(
            newest
        ):
            self._adopt(newest)
            return None
        return newest

    def _refresh_request(self, base: dict) -> httpx.Request:
        url = httpx.URL(f"{self.flow.api_base_url}/oauth/token")
        if not _secure(url):
            raise InsecureTransportError()
        return httpx.Request(
            "POST",
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": base["refresh_token"],
                **self.flow._client_params(),
            },
            headers={"Accept": "application/json"},
            extensions={"timeout": httpx.Timeout(self.refresh_timeout).as_dict()},
        )

    def _finish_refresh(self, response: httpx.Response, base: dict) -> None:
        if not (response.is_success or response.is_client_error):
            response.raise_for_status()
        try:
            token = dict(
                Client(self.flow.client_id).parse_request_body_response(response.text)
            )
        except (OAuth2Error, AttributeError, TypeError, ValueError) as e:
            raise RefreshFailedError(f"Token refresh failed: {e}") from e
        if response.is_client_error or not token.get("access_token"):
            raise RefreshFailedError(
                f"Token refresh failed: HTTP {response.status_code}, no usable access token"
            )
        token.setdefault("refresh_token", base["refresh_token"])
        self._adopt(token)
        self.flow.save_token(token)

    def _adopt(self, token: dict) -> None:
        self.token = token
        if self.on_token_updated:
            self.on_token_updated(token)
