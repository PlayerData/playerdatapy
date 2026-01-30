from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.gqlauth import AuthenticationType

import os
import asyncio
from datetime import datetime, timedelta
from queries.club_sessions_filtered_by_time_range import (
    club_sessions_filtered_by_time_range,
)

# Set the environment variables or hardcode them in the file if you prefer.
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLUB_ID = os.environ.get("CLUB_ID")

# Choose a time range for the query, in this case the last 30 days.
start_time = (datetime.now() - timedelta(days=30)).isoformat()
end_time = datetime.now().isoformat()

# Create a PlayerDataAPI instance for authentication.
api = PlayerDataAPI(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

# Run the queries.
response = asyncio.run(
    api.run_queries(
        "ClubSessionsFilteredByTimeRangeQuery",
        club_sessions_filtered_by_time_range(
            club_id=CLUB_ID,
            start_time_gteq=start_time,
            end_time_lteq=end_time,
        ),
    )
)
print(response)
