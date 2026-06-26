# Examples

Runnable scripts live in [`examples/`](https://github.com/PlayerData/playerdatapy/tree/main/examples).

## Pydantic (typed) — recommended

`PlayerDataAPI` + generated pydantic models. Type-safe field selection, no raw strings.

```python
from playerdatapy.playerdata_api import PlayerDataAPI

api = PlayerDataAPI(client_id="...", client_secret="...")
```

See [`examples/pydantic/quick_start.py`](https://github.com/PlayerData/playerdatapy/blob/main/examples/pydantic/quick_start.py) and the [`example_use.ipynb`](https://github.com/PlayerData/playerdatapy/blob/main/examples/pydantic/example_use.ipynb) notebook for session details, metrics, and raw-data queries.

## Direct GraphQL

Use `gqlclient.Client` directly when you want full control of the query string.

See [`examples/direct/quick_start.py`](https://github.com/PlayerData/playerdatapy/blob/main/examples/direct/quick_start.py).

## Sessions in last 30 days

End-to-end example: authenticate, build a time-windowed query, execute, print results.

```python
import asyncio
import os
from datetime import datetime, timedelta, timezone

from playerdatapy.gqlauth import GraphqlAuth, AuthenticationType
from playerdatapy.gqlclient import Client
from playerdatapy.constants import GRAPHQL_URL

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
CLUB_ID = os.environ["CLUB_ID"]

auth = GraphqlAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

end = datetime.now(timezone.utc)
start = end - timedelta(days=30)

query = """
query Sessions($clubIdEq: ID!, $startTimeGteq: ISO8601DateTime, $endTimeLteq: ISO8601DateTime) {
  sessions(filter: {
    clubIdEq: $clubIdEq,
    startTimeGteq: $startTimeGteq,
    endTimeLteq: $endTimeLteq
  }) {
    id
    startTime
    sessionParticipations {
      ... on TrainingSessionParticipation {
        athleteMetricSet {
          totalDistanceM
          maxSpeedKph
        }
      }
    }
  }
}
"""

variables = {
    "clubIdEq": CLUB_ID,
    "startTimeGteq": start.isoformat(),
    "endTimeLteq": end.isoformat(),
}


async def main():
    access_token = auth.authenticated_session.token["access_token"]
    client = Client(
        url=GRAPHQL_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response = await client.execute(query=query, variables=variables)
    sessions = client.get_data(response)["sessions"]
    for s in sessions:
        print(s["id"], s["startTime"])


asyncio.run(main())
```

For the typed/pydantic equivalent, see [`examples/pydantic/quick_start.py`](https://github.com/PlayerData/playerdatapy/blob/main/examples/pydantic/quick_start.py).
