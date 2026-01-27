from playerdatapy.gqlauth import GraphqlAuth
from playerdatapy.gqlclient import Client
from playerdatapy.gqlauth import AuthenticationType
import asyncio

# Build out the query string.
# Our GraphiQL Playground at https://app.playerdata.co.uk/api/graphiql/ is useful for building out and testing the query.
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

example_query = """
query Session($session_id: ID!) {
    session(id: $session_id) {
        id
        startTime
        endTime
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
        url="https://app.playerdata.co.uk/api/graphql",
        headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
    )
    response = await client.execute(
        query=example_query,
        variables={"session_id": session_id},
    )
    result = client.get_data(response)
    return result["session"]


if __name__ == "__main__":
    session_id = "an_example_session_id"
    result = asyncio.run(main(session_id))
    print(result)
