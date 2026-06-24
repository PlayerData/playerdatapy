# Authentication

PlayerData API uses **OAuth 2.0**. Two grant types depending on integration.

## Endpoints

| Purpose | URL |
|---------|-----|
| GraphQL API | `https://app.playerdata.co.uk/api/graphql` |
| OAuth Authorisation | `https://app.playerdata.co.uk/oauth/authorize` |
| OAuth Token/Refresh | `https://app.playerdata.co.uk/oauth/token` |
| Sign Out | `https://app.playerdata.co.uk/api/auth/identities/sign_out` |

## Grant types

**Authorisation Code Grant** — user-based access.

- Interactive sign-in
- Access mirrors what user sees in PlayerData app
- Read **and** write (queries + mutations)
- Redirect URIs must be pre-approved

**Client Credentials Grant** — server-to-server.

- No user sign-in, Client ID + Secret
- **Read-only** (queries only)
- Org-level data access
- Service account must be granted org access

## Permissions

Data access governed by **club staff membership**. To access a club's data, authenticated user/service must be listed as staff for that club. If missing, contact the club administrator.

## Tokens

- Access tokens expire after **2 hours**
- Authorisation Code Grant: refresh tokens issued — renew via `refresh_token` grant
- Client Credentials Grant: no refresh token — re-run flow for new token
- Refresh proactively before expiry

## Flows in `playerdatapy`

Three OAuth2 flows supported via `playerdatapy.gqlauth.AuthenticationType`:

| Flow | Use case |
|------|----------|
| `AUTHORISATION_CODE_FLOW` (default) | Confidential clients with a secret |
| `AUTHORISATION_CODE_FLOW_PCKE` | Public clients, no secret |
| `CLIENT_CREDENTIALS_FLOW` | Backend-to-backend |

Contact `support@playerdata.com` to request credentials.

## Env vars

```bash
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret
export CLUB_ID=your_club_id
```

## Client credentials (backend)

```python
from playerdatapy.gqlauth import GraphqlAuth, AuthenticationType

auth = GraphqlAuth(
    client_id="...",
    client_secret="...",
    type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)
```

## Authorisation code flow (PKCE)

```python
auth = GraphqlAuth(
    client_id="...",
    type=AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE,
)
```

Tokens are persisted to the path returned by `playerdatapy.auth.token_storage.default_token_path()`. Override with the `token_file=` argument.

## Regenerating the SDK

Codegen reads `schema.graphql` directly — no introspection token needed at codegen time. After bumping `schema.graphql`:

```bash
uv sync --group codegen
uv run ariadne-codegen
```

To refresh `schema.graphql` itself from the live API, run an introspection query separately and commit the result.
