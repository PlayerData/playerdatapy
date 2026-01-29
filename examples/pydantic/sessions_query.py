import asyncio
from datetime import datetime, timedelta

from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.custom_queries import Query
from playerdatapy.custom_fields import SessionInterface
from playerdatapy.input_types import SessionsSessionFilter
from playerdatapy.gqlauth import AuthenticationType
import os

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLUB_ID = os.environ.get("CLUB_ID")

# Create a PlayerDataAPI instance.
api = PlayerDataAPI(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

# Build out the query objects.
sessions_query = Query.sessions(
    filter=SessionsSessionFilter(
        clubIdEq=CLUB_ID,
        startTimeGteq=datetime.now() - timedelta(days=30),
        endTimeLteq=datetime.now(),
    )
).fields(
    SessionInterface.id,
    SessionInterface.start_time,
    SessionInterface.end_time,
)

# Run the query .
response = asyncio.run(api.run_queries("Sessions", sessions_query))
print(response)
