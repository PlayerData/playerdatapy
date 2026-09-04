# Errors

PlayerData API uses **standard HTTP status codes** per the HTTP specification. We do not intentionally return non-standard values.

Reference: [IANA HTTP status code registry](https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml).

If you encounter an unexpected or non-standard status code, report it to `support@playerdata.com` — treat as a bug.

## Common cases

| Code | Meaning |
|------|---------|
| `401 Unauthorized` | Missing or expired access token. Refresh token. |
| `403 Forbidden` | Authenticated but not staff on the requested club. |
| `400 Bad Request` | GraphQL validation error — bad query / variables. |
| `429 Too Many Requests` | Rate or complexity limit hit. Reduce query size. |
| `5xx` | Server-side fault. Retry with backoff. |

## GraphQL-level errors

A GraphQL request can return `200 OK` and still have failed. Always check the `errors` array, not just the status code.

`errors[].extensions.permissionError: true` means the authenticated caller lacks access to the requested resource. Which check failed depends on the grant:

- **Authorisation Code Grant** — the signed-in user is not a staff member of the requested club. Ask the club administrator to add them.
- **Client Credentials Grant** — the service account has not been granted access to the requested organisation. Organisation access is granted by PlayerData, so contact `support@playerdata.com` if you need more.

See [Permissions](auth.md#permissions) and [Troubleshooting](faq.md#troubleshooting).
