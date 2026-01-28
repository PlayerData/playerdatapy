import asyncio

from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.custom_queries import Query
from playerdatapy.custom_fields import (
    SessionInterface,
    SessionParticipationInterface,
    AthleteFields,
    EdgeDataFileFields,
)
from playerdatapy.enums import DatafileFormat
from playerdatapy.gqlauth import AuthenticationType
import os

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
SESSION_ID = os.environ.get("SESSION_ID")

# Create a PlayerDataAPI instance.
api = PlayerDataAPI(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

# Build out the query to get session participations and datafiles from a session.
session_query = Query.session(id=SESSION_ID).fields(
    SessionInterface.session_participations().fields(
        SessionParticipationInterface.id,
        SessionParticipationInterface.athlete().fields(
            AthleteFields.name,
        ),
        SessionParticipationInterface.datafiles().fields(
            EdgeDataFileFields.url(format=DatafileFormat.json),
        ),
    ),
)

# Run the query.
response = asyncio.run(api.run_queries("GetSessionParticipations", session_query))
print(response)
