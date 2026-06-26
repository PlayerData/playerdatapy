# PlayerData API

GraphQL API for accessing athlete, session, performance, and raw GPS data captured on the [PlayerData](https://playerdata.com/) platform.

Designed for technology partners, clubs, federations, analytics teams, research integrations.

## Quick links

<div class="grid cards" markdown>

- :material-api: **[API Overview](api/overview.md)** — endpoints, schema, sample queries
- :material-shield-lock: **[Authentication](auth.md)** — OAuth2 grant types
- :material-book-open-variant: **[Concepts](concepts.md)** — Organisation, Club, Session, Athlete
- :material-chart-line: **[Metrics](metrics.md)** — distance, speed, intensity, raw GPS
- :material-language-python: **[Python SDK](python/index.md)** — `pip install playerdatapy`
- :material-language-r: **[R wrapper](https://github.com/PlayerData/playerdatar)** — `remotes::install_github("PlayerData/playerdatar")`
- :material-application: **[Other Clients](clients.md)** — curl, JS, Go, anything that speaks HTTP

</div>

## At a glance

```graphql
query SessionDetails($id: ID!) {
  trainingSession(id: $id) {
    startTime
    sessionParticipations {
      athlete { name }
      athleteMetricSet {
        totalDistanceM
        maxSpeedKph
      }
    }
  }
}
```

GraphQL endpoint: `https://app.playerdata.co.uk/api/graphql`. Authenticate via OAuth2 — see [Authentication](auth.md).

## Resources

- Repo: [PlayerData/playerdatapy](https://github.com/PlayerData/playerdatapy) (official Python SDK)
- GraphiQL Playground: [app.playerdata.co.uk/api/graphiql](https://app.playerdata.co.uk/api/graphiql) — live schema, autocomplete, interactive queries. Runs against production; mutations affect live data.
- Support: support@playerdata.com
