# Clients

The PlayerData API is plain HTTPS + GraphQL. Any tool that can `POST` JSON works.

## Python — official SDK

`playerdatapy` is the recommended Python client. Handles OAuth2, pydantic-typed queries, raw GPS data.

```bash
pip install playerdatapy
```

See [Python SDK overview](python/index.md).

## R — official wrapper

[`playerdatar`](https://github.com/PlayerData/playerdatar) is the official R wrapper around the GraphQL API. Useful for analysts working in tidyverse workflows.

```r
# install from GitHub
remotes::install_github("PlayerData/playerdatar")
```

## Other languages

Use any GraphQL client or raw HTTP. The pattern is the same:

1. Obtain an access token via OAuth2 ([Authentication](auth.md))
2. POST a query to `https://app.playerdata.co.uk/api/graphql`
3. Pass the token as `Authorization: Bearer <token>`

### JavaScript / TypeScript

[`graphql-request`](https://github.com/jasonkuhrt/graphql-request) or `urql` / Apollo Client:

```ts
import { request } from 'graphql-request'

const endpoint = 'https://app.playerdata.co.uk/api/graphql'
const query = `
  query($id: ID!) {
    trainingSession(id: $id) { startTime }
  }
`

const data = await request({
  url: endpoint,
  document: query,
  variables: { id: '77395819-...' },
  requestHeaders: { Authorization: `Bearer ${token}` },
})
```

### Go

Use [`machinebox/graphql`](https://github.com/machinebox/graphql) or `Khan/genqlient` (typed codegen, similar to ariadne-codegen).

### Ruby / Java / C# / etc.

Any GraphQL client library will work. Or use the language's built-in HTTP client and POST the JSON envelope manually.

### Postman / Insomnia

Both speak GraphQL natively. Configure OAuth2 in the auth tab, paste the endpoint, send queries.

## Codegen from the schema

The schema is available via introspection. Most language ecosystems have a codegen tool that produces typed bindings:

| Language | Tool |
|---|---|
| Python | [`ariadne-codegen`](https://github.com/mirumee/ariadne-codegen) (what `playerdatapy` uses) |
| TypeScript | [`graphql-codegen`](https://the-guild.dev/graphql/codegen) |
| Go | [`Khan/genqlient`](https://github.com/Khan/genqlient) |
| Rust | [`graphql-client`](https://github.com/graphql-rust/graphql-client) |
| Kotlin / Java | [Apollo Kotlin](https://www.apollographql.com/docs/kotlin/) |
| Swift | [Apollo iOS](https://www.apollographql.com/docs/ios/) |
