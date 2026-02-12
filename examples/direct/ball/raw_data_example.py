"""
Fetch ball data recordings for a session and download raw JSON for each recording
that has a URL. Uses GraphQL for session/recording metadata and HTTP GET for the
raw data files.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import httpx

from playerdatapy.constants import API_BASE_URL
from playerdatapy.gqlauth import AuthenticationType, GraphqlAuth
from playerdatapy.gqlclient import Client

# -----------------------------------------------------------------------------
# Config (env or override below)
# -----------------------------------------------------------------------------
CLIENT_ID = os.environ.get("CLIENT_ID")
CLUB_ID = os.environ.get("CLUB_ID")
SESSION_DAYS = 30  # sessions from last N days

# -----------------------------------------------------------------------------
# GraphQL
# -----------------------------------------------------------------------------
SESSIONS_QUERY = """
query($clubIdEq: ID!, $startTimeGteq: ISO8601DateTime!, $endTimeLteq: ISO8601DateTime!) {
  sessions(filter: { clubIdEq: $clubIdEq, startTimeGteq: $startTimeGteq, endTimeLteq: $endTimeLteq }) {
    id
    startTime
    endTime
  }
}
"""

SESSION_BALL_DATA_QUERY = """
query($sessionId: ID!) {
  session(id: $sessionId) {
    id
    startTime
    endTime
    ballDataRecordings(withData: true) {
      id
      url(format: json)
      ball { id serialNumber }
    }
  }
}
"""


def _record_count(data: list | dict) -> int:
    if isinstance(data, list):
        return len(data)
    return len(data.get("records", []))


def _format_session_line(i: int, s: dict) -> str:
    """One line for a session: number, start–end, id."""
    start = s.get("startTime", "")[:19].replace("T", " ")
    end = s.get("endTime", "")[:19].replace("T", " ")
    sid = s.get("id", "")
    return f"  {i}. {start} – {end}  {sid}"


def _choose_session(sessions: list[dict]) -> dict | None:
    """
    Let the user choose a session when running interactively; otherwise use latest.
    Returns the chosen session dict or None if invalid/abort.
    """
    if not sessions:
        return None

    print("Sessions (most recent first):")
    for i, s in enumerate(sessions, start=1):
        print(_format_session_line(i, s))

    if not sys.stdin.isatty():
        chosen = sessions[0]
        print(f"Using latest session: {chosen['id']}")
        return chosen

    n = len(sessions)
    try:
        raw = input(f"Select session (1–{n}, or Enter for latest): ").strip()
        if not raw:
            return sessions[0]
        idx = int(raw)
        if 1 <= idx <= n:
            return sessions[idx - 1]
    except (ValueError, EOFError):
        pass
    print("Invalid choice; using latest session.")
    return sessions[0]


async def fetch_recordings_for_session(
    client: Client,
    session_id: str,
) -> list[dict] | None:
    """Return session dict with ballDataRecordings, or None if not found."""
    resp = await client.execute(
        query=SESSION_BALL_DATA_QUERY,
        variables={"sessionId": session_id},
    )
    data = client.get_data(resp)
    return data.get("session")


async def download_recording(
    http_client: httpx.AsyncClient,
    recording: dict,
    out_dir: str,
) -> bool:
    """Download one recording's raw JSON to out_dir. Returns True if saved, False if skipped."""
    url = recording.get("url")
    if not url:
        return False
    if url.startswith("/"):
        url = f"{API_BASE_URL.rstrip('/')}{url}"

    ball = recording.get("ball") or {}
    serial = ball.get("serialNumber", "?")

    try:
        r = await http_client.get(url)
        r.raise_for_status()
        raw = r.json()
    except httpx.HTTPStatusError as e:
        print(f"  Skip {recording['id']} (Ball {serial}): {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        print(f"  Skip {recording['id']} (Ball {serial}): {e}")
        return False

    if _record_count(raw) == 0:
        print(f"  Skip {recording['id']} (Ball {serial}): empty data")
        return False

    path = os.path.join(out_dir, f"{recording['id']}.json")
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"  Ball {serial}: {_record_count(raw)} records -> {path}")
    return True


async def main() -> None:
    auth = GraphqlAuth(
        client_id=CLIENT_ID,
        type=AuthenticationType.AUTHORISATION_CODE_FLOW_PCKE,
    )
    client = Client(
        url=f"{API_BASE_URL}/api/graphql",
        headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
    )

    now = datetime.now(timezone.utc)
    list_vars = {
        "clubIdEq": CLUB_ID,
        "startTimeGteq": (now - timedelta(days=SESSION_DAYS)).isoformat(),
        "endTimeLteq": now.isoformat(),
    }

    resp = await client.execute(query=SESSIONS_QUERY, variables=list_vars)
    sessions = client.get_data(resp).get("sessions") or []

    if not sessions:
        print("No sessions found.")
        return
    print(f"Found {len(sessions)} session(s) in last {SESSION_DAYS} days.")

    chosen = _choose_session(sessions)
    if not chosen:
        return

    session = await fetch_recordings_for_session(client, chosen["id"])
    if not session:
        print(f"Session {chosen['id']} not found.")
        return

    recordings_with_url = [
        r for r in (session.get("ballDataRecordings") or []) if r.get("url")
    ]
    if not recordings_with_url:
        print(f"No ball data recordings with URLs for session {session['id']}.")
        return

    out_dir = session["id"]
    os.makedirs(out_dir, exist_ok=True)
    print(f"Session {session['id']} ({session['startTime']} – {session['endTime']})")
    print(f"Downloading {len(recordings_with_url)} recording(s) to {out_dir}/")

    headers = {"Authorization": f"Bearer {auth._get_authentication_token()}"}
    async with httpx.AsyncClient(headers=headers) as http_client:
        ok = sum(
            await asyncio.gather(
                *[
                    download_recording(http_client, r, out_dir)
                    for r in recordings_with_url
                ]
            )
        )
    print(f"Done: {ok}/{len(recordings_with_url)} saved.")


if __name__ == "__main__":
    asyncio.run(main())
