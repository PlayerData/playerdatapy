import httpx
import pytest


@pytest.fixture
def mock_httpx(monkeypatch):
    """Route every httpx client created by the code under test to a handler."""

    def route(handler):
        transport = httpx.MockTransport(handler)

        class Client(httpx.Client):
            def __init__(self, **kwargs):
                super().__init__(transport=transport, **kwargs)

        class AsyncClient(httpx.AsyncClient):
            def __init__(self, **kwargs):
                super().__init__(transport=transport, **kwargs)

        monkeypatch.setattr(httpx, "Client", Client)
        monkeypatch.setattr(httpx, "AsyncClient", AsyncClient)

    return route
