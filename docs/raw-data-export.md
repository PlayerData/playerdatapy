# Raw Data Export

Per-sample data recorded during a session — GPS, local positioning (LPS/UWB), IMU, and heart rate — is downloadable as CSV or JSON.

Two mutations cover the two scopes:

| Mutation | Scope | Result |
|---|---|---|
| `requestRawDataExport` | One athlete in one session (a session participation) | A single file, or a zip for `FULL` + `CSV` |
| `requestSessionRawDataExport` | A whole session | Always a zip, one folder per athlete |

Both work the same way:

1. Call the mutation to request an export. Preparation starts in the background.
2. Call it again with the same arguments to poll. Repeat calls are safe and never duplicate work.
3. Once `status` is `READY`, the response carries a time-limited `downloadUrl`.

Prefer `requestSessionRawDataExport` over looping the per-participation mutation across a squad. Requesting a whole session requires staff-level access to the club that owns it; the per-participation mutation is the one for an athlete downloading their own data.

## Participation exports

```graphql
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestRawDataExport(sessionParticipationId: $id, dataType: $dataType, format: $format) {
    status
    downloadUrl
    errors { fullMessages }
  }
}
```

| Argument | Type | Description |
|---|---|---|
| `sessionParticipationId` | `ID!` | The session participation to export. IDs come from the `sessions` query. |
| `dataType` | `RawDataExportTypeEnum!` | `GPS`, `LPS` (or `UWB`), `IMU`, `IMU_ACCELERATION`, `HEARTRATE`, or `FULL` for every type recorded |
| `format` | `RawDataExportFormatEnum!` | `CSV` or `JSON` |

| Field | Type | Description |
|---|---|---|
| `status` | `RawDataStatusEnum!` | `READY`, `PROCESSING`, or `UNAVAILABLE` |
| `downloadUrl` | `String` | Time-limited link to the export file; present once `status` is `READY` |
| `errors` | `[ValidationError!]!` | Validation errors, e.g. an unknown `sessionParticipationId` |

`LPS` and `UWB` name the same data — local positioning recorded by an LPS installation. Use whichever you prefer; the exported files are always named `uwb.*`.

## Session exports

Arguments match `requestRawDataExport`, with a session ID in place of a participation ID.

```graphql
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestSessionRawDataExport(sessionId: $id, dataType: $dataType, format: $format) {
    status
    downloadUrl
    unavailableParticipationIds
    errors { fullMessages }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `status` | `RawDataStatusEnum!` | `READY`, `PROCESSING`, or `UNAVAILABLE` |
| `downloadUrl` | `String` | Time-limited link to the zip; present once `status` is `READY` |
| `unavailableParticipationIds` | `[ID!]!` | Participations left out of the export |
| `errors` | `[ValidationError!]!` | Validation errors, e.g. an unknown `sessionId` |

!!! note "Expect at least two calls"
    The call that finds every athlete's data ready is the one that starts building the zip, so it returns `PROCESSING`. `READY` arrives on a later poll.

### Which athletes are included

The zip contains a folder only for athletes whose data could be produced. Everyone else is listed in `unavailableParticipationIds` — usually because the type wasn't recorded for them, or because their device has not finished uploading.

- `unavailableParticipationIds` describes the file you are downloading. It is fixed when the zip is built and stays the same for as long as that export is reused.
- A session export does not wait for a slow-syncing device. That athlete is left out rather than holding up everyone else. To include them, request again once the reuse window has lapsed.

## Statuses

| Status | Meaning |
|---|---|
| `PROCESSING` | The export is being prepared. Poll again — every 15–30 seconds is a good default. |
| `READY` | The file is built. Download it from `downloadUrl`. |
| `UNAVAILABLE` | Participation scope: this data type was not recorded, e.g. no heart-rate monitor worn. Session scope: no athlete in the session recorded it. |

A participation with no data can report `PROCESSING` for up to 24 hours before it settles on `UNAVAILABLE`, so poll against a deadline rather than indefinitely.

## Export lifecycle

- **Download links expire after 15 minutes.** Call the mutation again for a fresh link.
- **Recent exports are reused for about 45 minutes.** Requesting the same export inside that window returns the already-built file straight away. After it, the export is rebuilt, so expect `PROCESSING` again briefly.
- **Preparation time varies** with session length and data type. A `FULL` export of a long session takes longer than one short data type.
- All timestamps in the data are **UTC**.

## Output formats

Participation scope:

| `dataType` | `format` | You get |
|---|---|---|
| A single type | `CSV` | One `.csv` for that type |
| A single type | `JSON` | `{ "gps": [ ...rows ] }` |
| `FULL` | `JSON` | Every recorded type in one document: `{ "gps": [...], "uwb": [...], ... }` |
| `FULL` | `CSV` | A `.zip` with one CSV per recorded type at the root — `gps.csv`, `imu.csv`, ... |

Session scope is always a zip, whatever the format, with one folder per athlete named after their session participation ID:

| `dataType` | `format` | Entries |
|---|---|---|
| A single type | `CSV` | `<participation-id>/gps.csv` |
| A single type | `JSON` | `<participation-id>/gps.json` |
| `FULL` | `JSON` | `<participation-id>/full.json` |
| `FULL` | `CSV` | `<participation-id>/gps.csv`, `<participation-id>/imu.csv`, ... |

```text
session_raw_data_<id>.zip
├── 0f9c2b41-8d3e-4a17-9c55-2e6b1f04a7d2/
│   ├── gps.csv
│   ├── imu.csv
│   └── heartrate.csv
└── 7b1e6a90-5c22-4f8b-b3d1-9a4c8e2f61b0/
    ├── gps.csv
    └── imu.csv
```

There are no nested zips to unpack — inner archives are flattened. An athlete listed in `unavailableParticipationIds` has no folder at all. Files inside a session zip are byte-identical to what the per-participation mutation returns, so the schemas below apply to both scopes.

## Data schemas

### GPS

Satellite positioning samples, roughly 10 per second.

| Column | Type | Description |
|---|---|---|
| `time` | integer | Sample time as Unix epoch milliseconds |
| `timestamp` | datetime | The same instant as ISO 8601 (UTC, millisecond precision) |
| `latitude` | number | Latitude in decimal degrees |
| `longitude` | number | Longitude in decimal degrees |
| `speed` | number | Speed in metres per second |
| `x` | number | Position on the local pitch coordinate system, metres |
| `y` | number | Position on the local pitch coordinate system, metres |
| `distance_delta` | number | Distance covered since the previous sample, metres |

```text
time,timestamp,latitude,longitude,speed,x,y,distance_delta
1784226737100,2026-07-16T18:32:17.100Z,51.446144,-0.089322,3.42,12.84,7.19,0.34
1784226737200,2026-07-16T18:32:17.200Z,51.446151,-0.089310,3.51,13.18,7.55,0.49
```

### LPS / UWB

Local positioning samples from an LPS installation.

| Column | Type | Description |
|---|---|---|
| `x` | number | Position on the local coordinate system, metres |
| `y` | number | Position on the local coordinate system, metres |
| `dx` | number | Change in `x` since the previous sample, metres |
| `dy` | number | Change in `y` since the previous sample, metres |
| `time` | integer | Sample time as Unix epoch milliseconds |
| `timestamp` | datetime | The same instant as ISO 8601 (UTC, millisecond precision) |
| `distance_delta` | number | Distance covered since the previous sample, metres |
| `speed` | number | Speed in metres per second |

### IMU

Inertial measurement samples, roughly 50 per second: acceleration plus device orientation.

| Column | Type | Description |
|---|---|---|
| `time` | datetime | Sample time, ISO 8601 (UTC, millisecond precision) |
| `acceleration_x` / `acceleration_y` / `acceleration_z` | number | Acceleration along each axis, m/s² |
| `orientation_x` / `orientation_y` / `orientation_z` / `orientation_w` | number | Device orientation as a unit quaternion |

### IMU_ACCELERATION

Per-axis acceleration samples, including which sensor recorded them.

| Column | Type | Description |
|---|---|---|
| `time` | datetime | Sample time, ISO 8601 (UTC, millisecond precision) |
| `x` / `y` / `z` | number | Acceleration along each axis |
| `sensor_location` | integer | Code identifying where on the body the sensor was worn |

### HEARTRATE

Roughly one sample per second.

| Column | Type | Description |
|---|---|---|
| `time` | datetime | Sample time, ISO 8601 (UTC, millisecond precision) |
| `mean_bpm` | number | Mean heart rate, beats per minute |

!!! note "Time columns"
    `GPS` and `LPS`/`UWB` carry both `time` (epoch milliseconds, convenient for numeric processing) and `timestamp` (ISO 8601). For `IMU`, `IMU_ACCELERATION`, and `HEARTRATE`, `time` is the ISO 8601 column.

The `satellites` column visible on some other raw-data endpoints is deliberately excluded from GPS and UWB exports.

## Python example

Authenticate, find a participation, request a GPS export, poll to a deadline, download.

```python
import asyncio
import os
import time

import httpx

from playerdatapy.constants import GRAPHQL_URL
from playerdatapy.gqlauth import AuthenticationType, GraphqlAuth
from playerdatapy.gqlclient import Client

auth = GraphqlAuth(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

client = Client(
    url=GRAPHQL_URL,
    headers={
        "Authorization": f"Bearer {auth.authenticated_session.token['access_token']}"
    },
)

REQUEST_RAW_DATA_EXPORT = """
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestRawDataExport(sessionParticipationId: $id, dataType: $dataType, format: $format) {
    status
    downloadUrl
    errors { fullMessages }
  }
}
"""


async def request_raw_data(
    session_participation_id: str,
    data_type: str = "GPS",
    format: str = "CSV",
    poll_interval: float = 15.0,
    timeout: float = 900.0,
) -> str:
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

        if result["errors"]:
            messages = [m for e in result["errors"] for m in e["fullMessages"]]
            raise RuntimeError(f"Export failed: {messages}")
        if result["status"] == "READY":
            return result["downloadUrl"]
        if result["status"] == "UNAVAILABLE":
            raise RuntimeError(f"No {data_type} data for this participation")
        if time.monotonic() + poll_interval > deadline:
            raise TimeoutError(f"Export still preparing after {timeout:.0f}s")

        await asyncio.sleep(poll_interval)


async def download(url: str, path: str) -> None:
    async with httpx.AsyncClient(timeout=60.0) as http:
        response = await http.get(url)
        response.raise_for_status()
        with open(path, "wb") as file:
            file.write(response.content)


async def main() -> None:
    url = await request_raw_data(os.environ["SESSION_PARTICIPATION_ID"])
    await download(url, "gps.csv")


asyncio.run(main())
```

The `timeout` matters: a participation with no data can report `PROCESSING` for up to 24 hours before it latches to `UNAVAILABLE`, so an unbounded poll loop can hang for a day.

### Reading a session zip

The session mutation polls identically. It returns a zip plus the athletes it left out, and individual CSVs can be read without extracting the archive.

```python
import zipfile

import polars as pl

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


def athlete_frame(zip_path: str, participation_id: str) -> pl.DataFrame:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(f"{participation_id}/gps.csv") as csv_file:
            return pl.read_csv(csv_file)
```

Polars ships as a `playerdatapy` dependency; `pandas.read_csv` accepts the same file object.

A runnable version of both flows, including session listing and zip inspection, is in [`examples/direct/raw_data_export.py`](https://github.com/PlayerData/playerdatapy/blob/main/examples/direct/raw_data_export.py).
