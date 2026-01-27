import os
import asyncio
from datetime import datetime, timedelta

from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.custom_queries import Query
from playerdatapy.custom_fields import SportDefinitionFields, SessionInterface
from playerdatapy.input_types import SessionsSessionFilter
from playerdatapy.gqlauth import AuthenticationType

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
CLUB_ID = "your_club_id"

# Create a PlayerDataAPI instance.
api = PlayerDataAPI(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

# Build out the query objects.
sports_query = Query.sports().fields(
    SportDefinitionFields.id,
    SportDefinitionFields.name,
    SportDefinitionFields.is_indoor,
    SportDefinitionFields.has_pitch_definition,
)

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

# Run the queries.
response = asyncio.run(api.run_queries("sports", sports_query, sessions_query))
print(response)
