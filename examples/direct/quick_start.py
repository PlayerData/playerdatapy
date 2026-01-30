from playerdatapy.gqlauth import GraphqlAuth
from playerdatapy.gqlclient import Client
from playerdatapy.gqlauth import AuthenticationType
from playerdatapy.constants import API_BASE_URL

import os
import asyncio
from datetime import datetime, timedelta

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLUB_ID = os.environ.get("CLUB_ID")

# Example usage of the GraphqlClient class.
auth = GraphqlAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

# Create a Client instance.
client = Client(
    url=f"{API_BASE_URL}/api/graphql",
    headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
)

# Build out the query string to get session details.
# Our GraphiQL Playground at https://app.playerdata.co.uk/api/graphiql/ is useful for building out and testing the query.
# This example query gets all sessions for a club in the last 30 days.
example_query = """
query($clubIdEq:ID!,$startTimeGteq:ISO8601DateTime,$endTimeLteq:ISO8601DateTime){
  sessions(filter: {clubIdEq:$clubIdEq, startTimeGteq:$startTimeGteq, endTimeLteq:$endTimeLteq}){
    id
    startTime
    endTime
  }
}
"""
startTimeGteq = (datetime.now() - timedelta(days=30)).isoformat()
endTimeLteq = datetime.now().isoformat()
variables = {
    "clubIdEq": CLUB_ID,
    "startTimeGteq": startTimeGteq,
    "endTimeLteq": endTimeLteq,
}


async def main():
    response = client.execute(query=example_query, variables=variables)
    result = await client.get_data(response)
    print(result["sessions"])


asyncio.run(main())
