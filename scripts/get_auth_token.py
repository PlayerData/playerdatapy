import sys
import os
from playerdatapy.auth.client_credentials_flow import ClientCredentialsFlow

client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")

if not client_id or not client_secret:
    print("Error: CLIENT_ID and CLIENT_SECRET must be set", file=sys.stderr)
    sys.exit(1)

try:
    client_credentials_flow = ClientCredentialsFlow(
        client_id=client_id,
        client_secret=client_secret,
    )
    token = client_credentials_flow.authenticate(save_token=False)
    auth_string = f"Bearer {token['access_token']}"
    with open(os.getenv("GITHUB_ENV"), "a") as f:
        f.write(f"AUTH_TOKEN={auth_string}\n")
    print("Bearer token obtained and set in AUTH_TOKEN environment variable.")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
