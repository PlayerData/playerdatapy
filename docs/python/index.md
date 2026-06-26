# Python SDK

`playerdatapy` — official Python client for the PlayerData GraphQL API.

```bash
pip install playerdatapy
# or
uv add playerdatapy
```

## Features

- **Typed:** pydantic models generated from the schema, autocompletion in your IDE
- **OAuth2 handled:** three flows (Authorisation Code, PKCE, Client Credentials), automatic token refresh
- **Async first:** built on `httpx`
- **Raw query escape hatch:** `Client.execute` if you want full control of the query string

## Get started

- [Quickstart](../quickstart.md) — install, authenticate, run your first query
- [Examples](../examples.md) — end-to-end runnable scripts
- [API Reference](../reference/index.md) — every public class with signatures, docstrings, inheritance

## When to use the SDK vs. raw HTTP

| Use the SDK | Use raw HTTP |
|---|---|
| You're in Python | You're in another language |
| You want IDE autocomplete on queries + results | You want minimal dependencies |
| You want OAuth2 + refresh handled for you | You already have an OAuth2 stack |

See [Clients](../clients.md) for non-Python access patterns.
