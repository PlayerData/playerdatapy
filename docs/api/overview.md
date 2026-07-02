# API Overview

PlayerData exposes a single GraphQL endpoint. Everything — sessions, athletes, metrics, raw GPS — is queryable from one URL.

## Endpoints

| Purpose | URL | Auth |
| --- | --- | --- |
| GraphQL API | `https://app.playerdata.co.uk/api/graphql` | Bearer token (OAuth2) |
| Schema SDL | `https://app.playerdata.co.uk/api/schema.graphql` | Public |
| GraphiQL playground | `https://app.playerdata.co.uk/api/graphiql` | Session login |

All API requests are `POST` with a JSON body containing a `query` (and optional `variables`). The SDL endpoint serves the full schema definition as `text/plain` — use it to regenerate typed clients without hitting introspection.

## Why GraphQL

- Strongly typed, self-documenting schema
- Single endpoint, one round-trip for nested data
- Clients request only the fields they need

Live schema explorer: [GraphiQL Playground](https://app.playerdata.co.uk/api/graphiql).

## Example: raw HTTP

```bash
curl -X POST https://app.playerdata.co.uk/api/graphql \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($id: ID!) { trainingSession(id: $id) { startTime } }",
    "variables": {"id": "77395819-b377-410a-8d9d-0ed27a771ad7"}
  }'
```

Response:

```json
{
  "data": {
    "trainingSession": {
      "startTime": "2024-05-19T14:47:00.000Z"
    }
  }
}
```

## Next steps

- **[Authentication](../auth.md)** — get an access token via OAuth2
- **[Concepts](../concepts.md)** — understand the schema's core types
- **[Metrics](../metrics.md)** — explore the data available per session
- **[Clients](../clients.md)** — Python SDK + access patterns for other languages
