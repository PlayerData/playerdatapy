import os

API_BASE_URL = os.environ.get("PLAYERDATA_BASE_URL", "https://app.playerdata.co.uk")
GRAPHQL_URL = os.environ.get("PLAYERDATA_GRAPHQL_URL", f"{API_BASE_URL}/api/graphql")
