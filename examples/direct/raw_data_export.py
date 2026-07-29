"""
Export raw session data via the requestRawDataExport and requestSessionRawDataExport
mutations. Picks the most recent session for a club, exports one athlete's data and the
whole session, then reads a single athlete's CSV out of the session zip.

Set CLIENT_ID, CLIENT_SECRET and CLUB_ID before running.
"""

from __future__ import annotations

import asyncio
import os
import time
import zipfile
from datetime import datetime, timedelta, timezone

import httpx
import polars as pl

from playerdatapy.constants import GRAPHQL_URL
from playerdatapy.gqlauth import AuthenticationType, GraphqlAuth
from playerdatapy.gqlclient import Client

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLUB_ID = os.environ.get("CLUB_ID")

DATA_TYPE = "GPS"
FORMAT = "CSV"
POLL_INTERVAL = 15.0

SESSIONS_QUERY = """
query($clubIdEq: ID!, $startTimeGteq: ISO8601DateTime, $endTimeLteq: ISO8601DateTime) {
  sessions(filter: {clubIdEq: $clubIdEq, startTimeGteq: $startTimeGteq, endTimeLteq: $endTimeLteq}) {
    id
    startTime
    sessionParticipations {
      id
      athlete { name }
    }
  }
}
"""

REQUEST_RAW_DATA_EXPORT = """
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestRawDataExport(sessionParticipationId: $id, dataType: $dataType, format: $format) {
    status
    downloadUrl
    errors { fullMessages }
  }
}
"""

REQUEST_SESSION_RAW_DATA_EXPORT = """
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestSessionRawDataExport(sessionId: $id, dataType: $dataType, format: $format) {
    status
    downloadUrl
    unavailableParticipationIds
    errors { fullMessages }
  }
}
"""


def _raise_on_errors(result: dict) -> None:
    if result["errors"]:
        messages = [m for e in result["errors"] for m in e["fullMessages"]]
        raise RuntimeError(f"Export failed: {messages}")


async def request_raw_data(
    client: Client,
    session_participation_id: str,
    data_type: str = DATA_TYPE,
    format: str = FORMAT,
    poll_interval: float = POLL_INTERVAL,
    timeout: float = 900.0,
) -> str:
    """Request one participation's raw data export and poll until it is ready.

    A participation with no data can report PROCESSING for up to 24 hours before it
    latches to UNAVAILABLE, so polling is always bounded by `timeout`.

    Args:
        client: An authenticated GraphQL client.
        session_participation_id: The session participation to export.
        data_type: GPS, LPS, UWB, IMU, IMU_ACCELERATION, HEARTRATE, or FULL.
        format: CSV or JSON.
        poll_interval: Seconds to wait between polls.
        timeout: Seconds to keep polling before giving up.

    Returns:
        A time-limited download URL for the export file.

    Raises:
        RuntimeError: The mutation returned validation errors, or the data is
            unavailable for this participation.
        TimeoutError: The export was still preparing when the deadline passed.
    """
    variables = {
        "id": session_participation_id,
        "dataType": data_type,
        "format": format,
    }
    deadline = time.monotonic() + timeout

    while True:
        response = await client.execute(
            query=REQUEST_RAW_DATA_EXPORT, variables=variables
        )
        result = client.get_data(response)["requestRawDataExport"]
        _raise_on_errors(result)

        if result["status"] == "READY":
            return result["downloadUrl"]
        if result["status"] == "UNAVAILABLE":
            raise RuntimeError(
                f"No {data_type} data for participation {session_participation_id}"
            )
        if time.monotonic() + poll_interval > deadline:
            raise TimeoutError(f"Export still preparing after {timeout:.0f}s")

        print(f"  preparing, polling again in {poll_interval:.0f}s")
        await asyncio.sleep(poll_interval)


async def request_session_raw_data(
    client: Client,
    session_id: str,
    data_type: str = DATA_TYPE,
    format: str = FORMAT,
    poll_interval: float = POLL_INTERVAL,
    timeout: float = 1800.0,
) -> tuple[str, list[str]]:
    """Request a whole session's raw data export and poll until it is ready.

    Expect at least two calls: the call that finds every athlete's data ready is the
    one that starts building the zip, so it returns PROCESSING.

    Args:
        client: An authenticated GraphQL client.
        session_id: The session to export.
        data_type: GPS, LPS, UWB, IMU, IMU_ACCELERATION, HEARTRATE, or FULL.
        format: CSV or JSON. A session export is a zip either way.
        poll_interval: Seconds to wait between polls.
        timeout: Seconds to keep polling before giving up.

    Returns:
        A time-limited download URL for the zip, and the participation IDs left
        out of it.

    Raises:
        RuntimeError: The mutation returned validation errors, or no athlete in
            the session recorded this data type.
        TimeoutError: The export was still preparing when the deadline passed.
    """
    variables = {"id": session_id, "dataType": data_type, "format": format}
    deadline = time.monotonic() + timeout

    while True:
        response = await client.execute(
            query=REQUEST_SESSION_RAW_DATA_EXPORT, variables=variables
        )
        result = client.get_data(response)["requestSessionRawDataExport"]
        _raise_on_errors(result)

        if result["status"] == "READY":
            return result["downloadUrl"], result["unavailableParticipationIds"]
        if result["status"] == "UNAVAILABLE":
            raise RuntimeError(f"No {data_type} data for session {session_id}")
        if time.monotonic() + poll_interval > deadline:
            raise TimeoutError(f"Export still preparing after {timeout:.0f}s")

        print(f"  preparing, polling again in {poll_interval:.0f}s")
        await asyncio.sleep(poll_interval)


async def download(url: str, path: str) -> None:
    """Download an export to a local file.

    Args:
        url: The download URL returned by an export mutation. Links expire 15
            minutes after they are issued.
        path: Where to write the file.
    """
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        response = await http_client.get(url)
        response.raise_for_status()
        with open(path, "wb") as file:
            file.write(response.content)


def athlete_frame(zip_path: str, participation_id: str) -> pl.DataFrame:
    """Read one athlete's GPS CSV out of a session zip without extracting it.

    Args:
        zip_path: Path to a downloaded session export.
        participation_id: The session participation whose folder to read.

    Returns:
        The athlete's GPS samples.
    """
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(f"{participation_id}/gps.csv") as csv_file:
            return pl.read_csv(csv_file)


async def latest_session(client: Client) -> dict | None:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    response = await client.execute(
        query=SESSIONS_QUERY,
        variables={
            "clubIdEq": CLUB_ID,
            "startTimeGteq": start.isoformat(),
            "endTimeLteq": end.isoformat(),
        },
    )
    sessions = client.get_data(response)["sessions"]
    if not sessions:
        return None
    return max(sessions, key=lambda s: s["startTime"])


async def main() -> None:
    auth = GraphqlAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
    )
    client = Client(
        url=GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {auth.authenticated_session.token['access_token']}"
        },
    )

    session = await latest_session(client)
    if not session:
        print("No sessions in the last 30 days.")
        return

    participations = session["sessionParticipations"]
    if not participations:
        print(f"Session {session['id']} has no participations.")
        return

    participation = participations[0]
    print(f"Session {session['id']} ({session['startTime']})")
    print(f"Exporting {DATA_TYPE} for {participation['athlete']['name']}")
    url = await request_raw_data(client, participation["id"])
    await download(url, "gps.csv")
    print("saved gps.csv")

    print(f"Exporting {DATA_TYPE} for the whole session")
    zip_url, unavailable = await request_session_raw_data(client, session["id"])
    await download(zip_url, "session_gps.zip")
    print("saved session_gps.zip")

    if unavailable:
        print(
            f"{len(unavailable)} athlete(s) had no {DATA_TYPE} data and were left out"
        )

    with zipfile.ZipFile("session_gps.zip") as archive:
        for name in archive.namelist():
            print(f"  {name}")

    if participation["id"] not in unavailable:
        frame = athlete_frame("session_gps.zip", participation["id"])
        print(frame.head())


if __name__ == "__main__":
    asyncio.run(main())
