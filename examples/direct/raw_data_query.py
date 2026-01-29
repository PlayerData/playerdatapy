from playerdatapy.gqlauth import GraphqlAuth
from playerdatapy.gqlclient import Client
from playerdatapy.gqlauth import AuthenticationType
import asyncio
from playerdatapy.constants import API_BASE_URL
import os

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
SESSION_ID = os.environ.get("SESSION_ID")

# Build out the query string to get session participations and datafiles from a session.
# Our GraphiQL Playground at https://app.playerdata.co.uk/api/graphiql/ is useful for building out and testing the query.
session_query = """
query GetSessionParticipations($session_id: ID!) {
    session(id: $session_id) {
        sessionParticipations {
            id
            athlete {
                name
            }
            datafiles {
                url(format: json)
            }
        }
    }
}
"""


async def main(session_id: str):
    auth = GraphqlAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
    )
    client = Client(
        url=f"{API_BASE_URL}/api/graphql",
        headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
    )
    response = await client.execute(
        query=session_query,
        variables={"session_id": session_id},
    )
    result = client.get_data(response)
    return result


if __name__ == "__main__":
    result = asyncio.run(main(SESSION_ID))
    print(result)
