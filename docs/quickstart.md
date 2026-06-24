# Quickstart

## 1. Install

```bash
uv add playerdatapy
```

## 2. Set credentials

```bash
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret
export CLUB_ID=your_club_id
```

## 3. Run a query

```python
import asyncio
import os
from datetime import datetime, timedelta, timezone

from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.gqlauth import AuthenticationType

api = PlayerDataAPI(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

end = datetime.now(timezone.utc)
start = end - timedelta(days=7)

response = asyncio.run(
    api.run_queries(
        "SessionsQuery",
        # Build query objects with helpers from examples/pydantic/queries
        # or directly from playerdatapy.custom_queries / custom_fields.
    )
)
print(response)
```

See [`examples/pydantic/quick_start.py`](https://github.com/PlayerData/playerdatapy/blob/main/examples/pydantic/quick_start.py) for a fully working example using the typed query helpers.

Build/test queries against [GraphiQL Playground](https://app.playerdata.co.uk/api/graphiql/).
