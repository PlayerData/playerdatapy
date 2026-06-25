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
