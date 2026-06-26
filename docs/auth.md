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

Under the **Authorisation Code Grant**, data access is governed by **club staff membership**: to access a club's data, the authenticated user must be listed as staff for that club. If missing, contact the club administrator.

**Client Credentials Grant** uses organisation-level access — service accounts must be explicitly granted org access by PlayerData.

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

## Client credentials — raw HTTP

```bash
curl -X POST https://app.playerdata.co.uk/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET"
```

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 7200
}
```

Use the `access_token` as `Authorization: Bearer <token>` on subsequent requests.

## Client credentials — Python SDK

```python
from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.gqlauth import AuthenticationType

api = PlayerDataAPI(
    client_id="...",
    client_secret="...",
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)
```

The SDK persists tokens to disk and refreshes proactively. See [Python SDK → Authentication](reference/authentication/GraphqlAuth.md).

## Authorisation Code flow — Python SDK (PKCE)

```python
from playerdatapy.gqlauth import GraphqlAuth, AuthenticationType

auth = GraphqlAuth(
    client_id="...",
    type=AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE,
)
```

SDK opens a browser, captures the redirect, exchanges code → token, stores it. Override the storage path with `token_file=`.

## Authorisation Code flow — manual (any language)

1. Send the user to:
   ```
   https://app.playerdata.co.uk/oauth/authorize
     ?response_type=code
     &client_id=$CLIENT_ID
     &redirect_uri=$REDIRECT_URI
   ```
2. Receive the `code` parameter on your registered redirect URI.
3. Exchange for tokens (confidential client — include `client_secret`):
   ```bash
   curl -X POST https://app.playerdata.co.uk/oauth/token \
     -d "grant_type=authorization_code" \
     -d "code=$CODE" \
     -d "client_id=$CLIENT_ID" \
     -d "client_secret=$CLIENT_SECRET" \
     -d "redirect_uri=$REDIRECT_URI"
   ```
   For public clients, omit `client_secret`.
4. Refresh later:
   ```bash
   curl -X POST https://app.playerdata.co.uk/oauth/token \
     -d "grant_type=refresh_token" \
     -d "refresh_token=$REFRESH_TOKEN" \
     -d "client_id=$CLIENT_ID"
   ```

## Env vars (used in examples)

```bash
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret
export CLUB_ID=your_club_id
```
