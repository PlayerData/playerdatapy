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
import asyncio, os
from playerdatapy.gqlauth import GraphqlAuth, AuthenticationType
from playerdatapy.gqlclient import Client
from playerdatapy.constants import API_BASE_URL

auth = GraphqlAuth(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

client = Client(
    url=f"{API_BASE_URL}/api/graphql",
    headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
)

query = """
query($clubIdEq: ID!) {
  sessions(filter: {clubIdEq: $clubIdEq}) {
    id
    startTime
  }
}
"""

async def main():
    response = await client.execute(query=query, variables={"clubIdEq": os.environ["CLUB_ID"]})
    print(client.get_data(response)["sessions"])

asyncio.run(main())
```

Build/test queries against [GraphiQL Playground](https://app.playerdata.co.uk/api/graphiql/).
