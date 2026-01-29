from playerdatapy.gqlauth import GraphqlAuth
from playerdatapy.gqlclient import Client
from playerdatapy.gqlauth import AuthenticationType
import asyncio
from playerdatapy.constants import API_BASE_URL
import os
from datetime import datetime, timedelta

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLUB_ID = os.environ.get("CLUB_ID")


# Build out the query string to get session details.
# Our GraphiQL Playground at https://app.playerdata.co.uk/api/graphiql/ is useful for building out and testing the query.
example_query = """
query($clubIdEq:ID!,$startTimeGteq:ISO8601DateTime,$endTimeLteq:ISO8601DateTime){
  sessions(filter: {clubIdEq:$clubIdEq, startTimeGteq:$startTimeGteq, endTimeLteq:$endTimeLteq}){
    id
    startTime
    endTime
  }
}
"""


async def main():
    auth = GraphqlAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
    )
    client = Client(
        url=f"{API_BASE_URL}/api/graphql",
        headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
    )
    startTimeGteq = (datetime.now() - timedelta(days=30)).isoformat()
    endTimeLteq = datetime.now().isoformat()
    variables = {
        "clubIdEq": CLUB_ID,
        "startTimeGteq": startTimeGteq,
        "endTimeLteq": endTimeLteq,
    }
    response = await client.execute(query=example_query, variables=variables)
    result = client.get_data(response)
    return result["sessions"]


if __name__ == "__main__":
    result = asyncio.run(main())
    print(result)
