import asyncio
import json
import threading
import time
from unittest.mock import patch
from urllib.parse import parse_qsl

import httpx
import pytest
from oauthlib.oauth2 import InsecureTransportError

from playerdatapy.auth.base_flow import BaseAuthFlow
from playerdatapy.auth.errors import RefreshFailedError
from playerdatapy.auth.token_refresher import TokenRefresher

API_BASE_URL = "https://app.playerdata.co.uk"
GRAPHQL_URL = f"{API_BASE_URL}/api/graphql"
OTHER_GRAPHQL_URL = "https://graphql.example.com/api/graphql"
LOCAL_GRAPHQL_URL = "http://localhost:8000/api/graphql"


def _token(access="old-access", refresh="old-refresh", expires_in=-60):
    token = {
        "access_token": access,
        "token_type": "Bearer",
        "expires_at": time.time() + expires_in,
    }
    if refresh is not None:
        token["refresh_token"] = refresh
    return token


class FakeServer:
    """Token endpoint that rotates refresh tokens, plus a GraphQL endpoint."""

    def __init__(self):
        self.rejected_access_tokens = set()
        self.refresh_delay = 0.0
        self.refresh_response: httpx.Response | None = None
        self.refresh_error: Exception | None = None
        self.refresh_requests: list[httpx.Request] = []
        self.api_authorizations: list[str | None] = []

    def refresh_forms(self):
        return [dict(parse_qsl(r.content.decode())) for r in self.refresh_requests]

    def handler(self, request: httpx.Request):
        """Answer the request; on an event loop the token endpoint yields first."""
        if request.url.path == "/oauth/token":
            self.refresh_requests.append(request)
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                time.sleep(self.refresh_delay)
                return self._refresh(request)
            return self._async_refresh(request)

        authorization = request.headers.get("Authorization")
        self.api_authorizations.append(authorization)
        if authorization and authorization.removeprefix("Bearer ") in (
            self.rejected_access_tokens
        ):
            return httpx.Response(401, json={"error": "unauthorized"})
        return httpx.Response(200, json={"data": {}})

    async def _async_refresh(self, request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(self.refresh_delay)
        return self._refresh(request)

    def _refresh(self, request: httpx.Request) -> httpx.Response:
        if self.refresh_error is not None:
            raise self.refresh_error
        if self.refresh_response is not None:
            return self.refresh_response

        n = len(self.refresh_requests)
        return httpx.Response(
            200,
            json={
                "access_token": f"new-access-{n}",
                "refresh_token": f"new-refresh-{n}",
                "token_type": "Bearer",
                "expires_in": 7200,
            },
        )


@pytest.fixture
def server(mock_httpx):
    server = FakeServer()
    mock_httpx(server.handler)
    return server


@pytest.fixture
def flow(tmp_path):
    return BaseAuthFlow("test_client", tmp_path / "token.json", API_BASE_URL)


def _refresher(flow, token=None, **kwargs):
    token = token or _token()
    flow.save_token(token)
    kwargs.setdefault("allowed_urls", [API_BASE_URL, GRAPHQL_URL])
    return TokenRefresher(flow, token, **kwargs)


def _saved(flow):
    return json.loads(flow.token_file.read_text())


async def _send(refresher, url=GRAPHQL_URL, method="POST"):
    async with httpx.AsyncClient(auth=refresher) as client:
        return await client.request(method, url)


class TestTokenRefresherProactiveRefresh:
    """An expired token is refreshed before the request is sent."""

    async def test_expired_token_is_refreshed_once_used_and_saved(self, server, flow):
        updates = []
        refresher = _refresher(flow, on_token_updated=updates.append)

        response = await _send(refresher)

        assert response.status_code == 200
        assert server.refresh_forms() == [
            {
                "grant_type": "refresh_token",
                "refresh_token": "old-refresh",
                "client_id": "test_client",
            }
        ]
        assert server.refresh_requests[0].headers["Accept"] == "application/json"
        assert server.refresh_requests[0].extensions["timeout"]["read"] == 15
        assert server.api_authorizations == ["Bearer new-access-1"]
        assert _saved(flow)["refresh_token"] == "new-refresh-1"
        assert "expires_at" in _saved(flow)
        assert [u["access_token"] for u in updates] == ["new-access-1"]

    async def test_refresh_sends_client_secret_when_set(self, server, flow):
        flow.client_secret = "shh"

        await _send(_refresher(flow))

        assert server.refresh_forms()[0]["client_secret"] == "shh"

    @pytest.mark.parametrize(
        ("expires_in", "refreshes"), [(29, 1), (31, 0)], ids=["within", "outside"]
    )
    async def test_refreshes_within_leeway_only(
        self, server, flow, expires_in, refreshes
    ):
        await _send(_refresher(flow, _token(expires_in=expires_in)))

        assert len(server.refresh_requests) == refreshes

    async def test_response_without_refresh_token_keeps_previous(self, server, flow):
        server.refresh_response = httpx.Response(
            200, json={"access_token": "new-access", "expires_in": 7200}
        )

        await _send(_refresher(flow))

        assert _saved(flow)["access_token"] == "new-access"
        assert _saved(flow)["refresh_token"] == "old-refresh"

    async def test_streamed_refresh_response_is_read(self, server, flow):
        body = json.dumps({"access_token": "new-access", "expires_in": 7200})
        server.refresh_response = httpx.Response(
            200, stream=httpx.ByteStream(body.encode())
        )

        await _send(_refresher(flow))

        assert server.api_authorizations == ["Bearer new-access"]

    async def test_token_without_refresh_token_is_sent_as_is(self, server, flow):
        server.rejected_access_tokens = {"old-access"}

        response = await _send(_refresher(flow, _token(refresh=None)))

        assert response.status_code == 401
        assert server.refresh_requests == []
        assert server.api_authorizations == ["Bearer old-access"]


class TestTokenRefresherSingleRefresh:
    """A single-use refresh token is only ever spent once."""

    @pytest.mark.parametrize(
        ("expires_in", "rejected"),
        [(-60, set()), (3600, {"old-access"})],
        ids=["expired", "unauthorized"],
    )
    async def test_concurrent_requests_refresh_once(
        self, server, flow, expires_in, rejected
    ):
        server.rejected_access_tokens = rejected
        refresher = _refresher(flow, _token(expires_in=expires_in))

        async with httpx.AsyncClient(auth=refresher) as client:
            responses = await asyncio.gather(
                *[client.post(GRAPHQL_URL) for _ in range(5)]
            )

        assert [r.status_code for r in responses] == [200] * 5
        assert len(server.refresh_requests) == 1

    async def test_two_refreshers_share_one_refresh(self, server, flow):
        refreshers = [_refresher(flow), _refresher(flow)]

        responses = await asyncio.gather(*[_send(r) for r in refreshers])

        assert [r.status_code for r in responses] == [200, 200]
        assert len(server.refresh_requests) == 1

    def test_ensure_fresh_in_threads_refreshes_once(self, server, flow):
        server.refresh_delay = 0.1
        refresher = _refresher(flow)
        barrier = threading.Barrier(2)
        tokens = []

        def run():
            barrier.wait()
            tokens.append(refresher.ensure_fresh()["access_token"])

        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert tokens == ["new-access-1", "new-access-1"]
        assert len(server.refresh_requests) == 1

    def test_sync_client_is_rejected(self, server, flow):
        with httpx.Client(auth=_refresher(flow)) as client:
            with pytest.raises(TypeError, match="AsyncClient"):
                client.post(GRAPHQL_URL)


class TestTokenRefresherUnauthorized:
    """A 401 from the API triggers at most one refresh and one retry."""

    async def test_401_refreshes_and_retries_once(self, server, flow):
        server.rejected_access_tokens = {"old-access"}

        response = await _send(_refresher(flow, _token(expires_in=3600)))

        assert response.status_code == 200
        assert len(server.refresh_requests) == 1
        assert server.api_authorizations == ["Bearer old-access", "Bearer new-access-1"]

    async def test_second_401_is_returned(self, server, flow):
        server.rejected_access_tokens = {"old-access", "new-access-1"}

        response = await _send(_refresher(flow, _token(expires_in=3600)))

        assert response.status_code == 401
        assert len(server.refresh_requests) == 1
        assert len(server.api_authorizations) == 2

    async def test_401_without_expires_at_refreshes(self, server, flow):
        server.rejected_access_tokens = {"old-access"}
        token = _token()
        del token["expires_at"]

        response = await _send(_refresher(flow, token))

        assert response.status_code == 200
        assert len(server.refresh_requests) == 1


class TestTokenRefresherErrors:
    """A failed refresh raises, keeps the old token and releases the locks."""

    @pytest.mark.parametrize(
        ("outcome", "error", "match"),
        [
            (
                httpx.Response(400, json={"error": "invalid_grant"}),
                RefreshFailedError,
                "invalid_grant",
            ),
            (httpx.Response(429), RefreshFailedError, None),
            (httpx.Response(503), httpx.HTTPStatusError, None),
            (httpx.ConnectError("unreachable"), httpx.ConnectError, None),
            (
                httpx.Response(200, json={"token_type": "Bearer"}),
                RefreshFailedError,
                None,
            ),
            (httpx.Response(200, json={"access_token": ""}), RefreshFailedError, None),
            (
                httpx.Response(400, json={"access_token": "new-access"}),
                RefreshFailedError,
                None,
            ),
            (httpx.Response(200, content=b"null"), RefreshFailedError, None),
            (httpx.Response(200, content=b"[]"), RefreshFailedError, None),
            (
                httpx.Response(200, json={"access_token": "x", "expires_in": "soon"}),
                RefreshFailedError,
                None,
            ),
        ],
        ids=[
            "rejected",
            "rate-limited",
            "unavailable",
            "unreachable",
            "missing-token",
            "empty-token",
            "client-error-with-token",
            "null-body",
            "list-body",
            "bad-expiry",
        ],
    )
    async def test_failed_refresh(self, server, flow, outcome, error, match):
        if isinstance(outcome, Exception):
            server.refresh_error = outcome
        else:
            server.refresh_response = outcome
        refresher = _refresher(flow, lock_timeout=1)

        async with httpx.AsyncClient(auth=refresher) as client:
            with pytest.raises(error, match=match):
                await client.post(GRAPHQL_URL)
            saved = _saved(flow)
            server.refresh_response = server.refresh_error = None
            retried = await client.post(GRAPHQL_URL)

        assert saved["refresh_token"] == "old-refresh"
        assert retried.status_code == 200

    def test_refresh_after_failed_save_uses_in_memory_token(self, server, flow):
        server.refresh_response = httpx.Response(
            200,
            json={
                "access_token": "unsaved-access",
                "refresh_token": "unsaved-refresh",
                "expires_in": 10,
            },
        )
        refresher = _refresher(flow)
        with patch.object(flow, "save_token", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                refresher.ensure_fresh()
        server.refresh_response = None

        refresher.ensure_fresh()

        assert server.refresh_forms()[1]["refresh_token"] == "unsaved-refresh"

    async def test_cancelled_refresh_releases_locks(self, server, flow):
        server.refresh_delay = 3600
        refresher = _refresher(flow, lock_timeout=1)

        async with httpx.AsyncClient(auth=refresher) as client:
            task = asyncio.create_task(client.post(GRAPHQL_URL))
            while not server.refresh_requests:
                await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            server.refresh_delay = 0
            response = await client.post(GRAPHQL_URL)

        assert response.status_code == 200

    def test_refresh_over_plain_http_is_refused(self, server, flow):
        flow.api_base_url = "http://app.playerdata.co.uk"

        with pytest.raises(InsecureTransportError):
            _refresher(flow).ensure_fresh()

        assert server.refresh_requests == []


@pytest.mark.parametrize(
    ("url", "authorization"),
    [
        ("https://storage.example.com/file", None),
        ("http://app.playerdata.co.uk/api/graphql", None),
        (OTHER_GRAPHQL_URL, "Bearer new-access-1"),
        (LOCAL_GRAPHQL_URL, "Bearer new-access-1"),
    ],
    ids=["other-host", "plain-http", "separate-graphql-host", "localhost-http"],
)
async def test_only_allowed_urls_get_the_token(server, flow, url, authorization):
    refresher = _refresher(
        flow, allowed_urls=[API_BASE_URL, OTHER_GRAPHQL_URL, LOCAL_GRAPHQL_URL]
    )

    await _send(refresher, url, "GET")

    assert server.api_authorizations == [authorization]
    assert len(server.refresh_requests) == (authorization is not None)
