import os

DEFAULT_BASE_URL = "https://app.playerdata.co.uk"


def graphql_url_for(base_url: str) -> str:
    return f"{base_url}/api/graphql"


API_BASE_URL = os.environ.get("PLAYERDATA_BASE_URL", DEFAULT_BASE_URL)
GRAPHQL_URL = os.environ.get("PLAYERDATA_GRAPHQL_URL", graphql_url_for(API_BASE_URL))
