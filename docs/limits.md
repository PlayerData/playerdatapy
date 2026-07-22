# Pagination & limits

## Rate limits

The API is rate limited to keep the platform stable. Build clients to stay within these budgets and to back off when throttled.

| Limit | Budget |
|-------|--------|
| Per IP address | 150 requests / 5 seconds |
| Per access token | 100 requests / 5 seconds |
| Concurrent GraphQL requests | 20 in flight |

- Per-IP and per-token limits apply over a rolling 5-second window.
- The per-token limit is your core API budget — pace sustained traffic against it.
- Keep no more than 20 GraphQL requests in flight at once.

### Handling `429 Too Many Requests`

When you exceed a limit the API responds with `429 Too Many Requests`. Well-behaved clients:

- Stop issuing new requests and let in-flight ones drain.
- Retry with **exponential backoff and jitter** — increasing delays plus a random offset — rather than retrying immediately.
- Bound concurrency to 20 and keep sustained request rate below the per-token budget to avoid repeat 429s.

## Pagination

- Default + maximum page size: **30 records**
- Use `offset` and `limit` parameters to page

```graphql
sessions(filter: {...}, offset: 0, limit: 30) { id }
```

## Query complexity

Complexity limits enforced to protect platform stability. Large or deeply nested queries may fail.

**Best practice:**

- Split large data requests into smaller queries
- Avoid requesting full metrics across many sessions in one query
- Page through sessions, then fetch metrics per page
