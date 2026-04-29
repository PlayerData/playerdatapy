import os
import secrets
import threading
import time
import urllib.parse
import webbrowser

import requests
from flask import Flask, redirect, request

app = Flask(__name__)

CLIENT_ID = os.environ.get("CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "your_client_secret")
REDIRECT_URI = "http://localhost:8000"
AUTH_URL = "https://app.playerdata.co.uk/api/oauth/authorize"
TOKEN_URL = "https://app.playerdata.co.uk/api/oauth/token"
GRAPHQL_URL = "https://app.playerdata.co.uk/api/graphql"

_state_store = {}


@app.route("/")
def index():
    if request.args.get("error"):
        return f"Authorization error: {request.args['error']}", 400

    if request.args.get("code"):
        if request.args.get("state") != _state_store.get("state"):
            return "State mismatch", 400

        resp = requests.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": request.args["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        })
        if not resp.ok:
            return f"Token exchange failed: {resp.text}", 400

        access_token = resp.json()["access_token"]
        return redirect(f"/me?token={access_token}")

    # CORRECT: start at the authorize endpoint, not the login page
    state = secrets.token_urlsafe(16)
    _state_store["state"] = state
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "public",
        "prompt": "consent",
        "state": state,
    }
    return redirect(AUTH_URL + "?" + urllib.parse.urlencode(params))


@app.route("/me")
def me():
    access_token = request.args.get("token")
    if not access_token:
        return redirect("/")

    resp = requests.post(
        GRAPHQL_URL,
        json={"query": "{ currentPerson { name } }"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if not resp.ok:
        return f"GraphQL request failed: {resp.text}", 400

    name = resp.json()["data"]["currentPerson"]["name"]
    return f"""<!DOCTYPE html>
<html>
<head><title>Hello</title>
<style>
  body {{ font-family: sans-serif; max-width: 500px; margin: 100px auto; text-align: center; }}
  h1 {{ font-size: 2em; }}
</style>
</head>
<body>
  <h1>Hello, {name}!</h1>
  <p>Successfully authenticated with PlayerData.</p>
</body>
</html>"""


def _open_browser():
    time.sleep(1)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(port=8000, debug=True, use_reloader=False)
