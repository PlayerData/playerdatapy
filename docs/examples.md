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

```python
from datetime import datetime, timedelta

end = datetime.utcnow()
start = end - timedelta(days=30)

variables = {
    "clubIdEq": CLUB_ID,
    "startTimeGteq": start.isoformat() + "Z",
    "endTimeLteq": end.isoformat() + "Z",
}
```
