# PlayerDataPy

Typed Python client for the [PlayerData](https://playerdata.com/) GraphQL API.

## Install

```bash
uv add playerdatapy
```

Or via pip:

```bash
pip install playerdatapy
```

## At a glance

```python
from playerdatapy.playerdata_api import PlayerDataAPI

api = PlayerDataAPI(client_id="...", client_secret="...")
```

See [Authentication](auth.md), [Quickstart](quickstart.md), [Examples](examples.md), and the full [API Reference](api.md).

## Resources

- Repo: [PlayerData/playerdatapy](https://github.com/PlayerData/playerdatapy)
- GraphQL endpoint: `https://app.playerdata.co.uk/api/graphql`
- GraphiQL Playground: [app.playerdata.co.uk/api/graphiql](https://app.playerdata.co.uk/api/graphiql) — live schema, autocomplete, interactive queries. Runs against production; mutations affect live data.
- Support: support@playerdata.com
