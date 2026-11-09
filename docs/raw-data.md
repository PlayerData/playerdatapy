# Raw data exports

Download the per-sample data recorded in a session (GPS, LPS/UWB, IMU and heart rate) as CSV or JSON.

There are two mutations:

- `requestRawDataExport` exports one athlete in one session (a **session participation**).
- `requestSessionRawDataExport` exports a whole **session** as one zip, with a folder per athlete. Use it instead of calling the per-participation mutation once for each athlete.

Both work the same way:

1. Call the mutation to request an export. Preparation starts in the background.
2. Call it again with the same arguments to check progress. Repeating the call is always safe: it returns the file it already built, and only rebuilds when newer data has been prepared.
3. When the export is ready, the response contains a download link valid for 15 minutes.

!!! note "Replaces `datafiles { url }`"
    Use these mutations instead of `SessionParticipation.datafiles { url(format: json) }`. That field's `format` argument is deprecated and JSON datafiles from it will stop being available to third-party integrations.

## `requestRawDataExport`

```graphql
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestRawDataExport(sessionParticipationId: $id, dataType: $dataType, format: $format) {
    status        # READY | PROCESSING | UNAVAILABLE | NOT_FOUND
    downloadUrl   # present once status is READY
    errors { fullMessages }
  }
}
```

| Argument | Type | Description |
|---|---|---|
| `sessionParticipationId` | `ID!` | The session participation to export. Available from `session { sessionParticipations { id } }` |
| `dataType` | `RawDataExportTypeEnum!` | `GPS`, `LPS` (or `UWB`), `IMU`, `IMU_ACCELERATION`, `HEARTRATE`, or `FULL` for every type recorded |
| `format` | `RawDataExportFormatEnum!` | `CSV` or `JSON` |

`LPS` and `UWB` are two names for the same data: local positioning recorded by an LPS installation.

| Status | Meaning |
|---|---|
| `PROCESSING` | The export is being prepared. Call again to poll; every 15–30 seconds is a good interval. If the athlete's device has not finished uploading, this can last until 24 hours after the session ends, after which the status becomes `UNAVAILABLE` |
| `READY` | Download the file from `downloadUrl` |
| `UNAVAILABLE` | This data type was not recorded for this participation (for example, no heart-rate strap worn), or the data could not be prepared |
| `NOT_FOUND` | No session participation with that ID exists. `errors` carries `Session participation not found` |

## `requestSessionRawDataExport`

Takes a session ID instead of a participation ID and always returns a zip with one folder per athlete. Requesting a whole session requires staff-level access to the club that owns it.

```graphql
mutation($id: ID!, $dataType: RawDataExportTypeEnum!, $format: RawDataExportFormatEnum!) {
  requestSessionRawDataExport(sessionId: $id, dataType: $dataType, format: $format) {
    status                        # READY | PROCESSING | UNAVAILABLE | NOT_FOUND
    downloadUrl                   # present once status is READY
    unavailableParticipationIds   # athletes left out of the export
    errors { fullMessages }
  }
}
```

- **Expect at least two calls.** The call that finds every athlete's data ready starts building the zip and returns `PROCESSING`; `READY` arrives on a later poll.
- **A slow device does not hold up the session.** An athlete whose data could not be produced (type not recorded, or device not yet synced) has no folder and is listed in `unavailableParticipationIds`. Request again once their data has arrived to include them.
- `UNAVAILABLE` means no athlete in the session recorded this data type.

## Export lifecycle

- **Download links expire after 15 minutes.** Call the mutation again for a fresh link.
- **Recent exports are reused.** Repeating a request within about 45 minutes returns the already-built file straight away, unless newer data has been prepared for that athlete, in which case it is rebuilt.
- **`FULL` waits for the whole session.** It is built once the session has finished and every recorded type has been prepared, so it is never missing a type that was still processing. If a type never arrives, the wait ends after about 15 minutes and the export is built from the types that did. Single types are not held back this way.
- **Live sessions.** Single types can be exported while a session is in progress, but the file is a snapshot that keeps being rebuilt as new data arrives. Data uploaded after the session supersedes what was streamed live, so export once the session has finished for complete, stable data.
- All timestamps are **UTC**.

## Output formats

| `dataType` | `format` | Participation export | Session export |
|---|---|---|---|
| Single type (e.g. `GPS`) | `CSV` | `gps.csv` | zip of `<participation-id>/gps.csv` |
| Single type | `JSON` | `{ "gps": [ …rows ] }` | zip of `<participation-id>/gps.json` |
| `FULL` | `JSON` | `{ "gps": [...], "uwb": [...], … }` with only the recorded types | zip of `<participation-id>/full.json` |
| `FULL` | `CSV` | zip with one CSV per recorded type | zip with one CSV per recorded type, per athlete |

Each file inside a session zip is exactly what the participation export would return, so the schemas below apply to both.

## Data schemas

### GPS

Satellite positioning samples, approximately 10 per second.

| Column | Type | Description |
|---|---|---|
| `time` | integer | Unix epoch milliseconds |
| `timestamp` | datetime | The same instant as ISO 8601 (UTC, milliseconds) |
| `latitude` | number | Decimal degrees |
| `longitude` | number | Decimal degrees |
| `speed` | number | Metres per second |
| `x` | number | UTM **northing**, metres (absolute, not pitch-relative) |
| `y` | number | UTM **easting**, metres (absolute, not pitch-relative) |
| `distance_delta` | number | Distance since the previous sample, metres |
| `satellites` | integer | Number of satellites used for the fix |

GPS `x`/`y` are each sample's latitude/longitude projected into the UTM zone covering the session:

- The axes are swapped relative to the usual convention: `x` is the northing, `y` the easting.
- The zone is not included. Derive it from `latitude`/`longitude` if you need to reproject.
- Southern-hemisphere northings are negative, without the standard +10,000,000 false northing. Add it back before using PROJ, GDAL or similar.

For pitch-relative coordinates, compute them from `latitude`/`longitude` against your own pitch corners.

### LPS / UWB

| Column | Type | Description |
|---|---|---|
| `x`, `y` | number | Position on the local coordinate system, metres |
| `dx`, `dy` | number | Velocity along `x` and `y`, metres per second |
| `time` | integer | Unix epoch milliseconds |
| `timestamp` | datetime | The same instant as ISO 8601 (UTC, milliseconds) |
| `distance_delta` | number | Distance since the previous sample, metres |
| `speed` | number | Metres per second, the magnitude of (`dx`, `dy`) |

### IMU

| Column | Type | Description |
|---|---|---|
| `time` | datetime | ISO 8601 (UTC, milliseconds) |
| `acceleration_x`, `acceleration_y`, `acceleration_z` | number | Acceleration per axis, m/s² |
| `orientation_x`, `orientation_y`, `orientation_z`, `orientation_w` | number | Device orientation as a unit quaternion |

### IMU_ACCELERATION

| Column | Type | Description |
|---|---|---|
| `time` | datetime | ISO 8601 (UTC, milliseconds) |
| `x`, `y`, `z` | number | Acceleration per axis |
| `sensor_location` | integer | Code for where on the body the sensor was worn |

### HEARTRATE

| Column | Type | Description |
|---|---|---|
| `time` | datetime | ISO 8601 (UTC, milliseconds) |
| `mean_bpm` | number | Mean heart rate, beats per minute |

## Python example

Requests a GPS export for one participation, polls until it is ready, and loads the CSV. See [`examples/pydantic/queries/request_raw_data_export.py`](https://github.com/PlayerData/playerdatapy/blob/main/examples/pydantic/queries/request_raw_data_export.py) for the mutation helper.

```python
import asyncio
import io
import os

import httpx
import polars as pl

from playerdatapy.custom_fields import RequestRawDataExportPayloadFields, ValidationErrorFields
from playerdatapy.custom_mutations import Mutation
from playerdatapy.enums import RawDataExportFormatEnum, RawDataExportTypeEnum
from playerdatapy.gqlauth import AuthenticationType
from playerdatapy.playerdata_api import PlayerDataAPI

api = PlayerDataAPI(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)


async def export_gps(session_participation_id: str, timeout_s: float = 900) -> pl.DataFrame:
    mutation = Mutation.request_raw_data_export(
        session_participation_id=session_participation_id,
        data_type=RawDataExportTypeEnum.GPS,
        format=RawDataExportFormatEnum.CSV,
    ).fields(
        RequestRawDataExportPayloadFields.status,
        RequestRawDataExportPayloadFields.download_url,
        RequestRawDataExportPayloadFields.errors().fields(ValidationErrorFields.full_messages),
    )

    deadline = asyncio.get_running_loop().time() + timeout_s
    while True:
        result = (await api.run_mutations("RequestRawDataExport", mutation))["requestRawDataExport"]
        if result["errors"]:
            raise RuntimeError(result["errors"])
        if result["status"] == "READY":
            break
        if result["status"] in ("UNAVAILABLE", "NOT_FOUND"):
            raise RuntimeError(f"No GPS export: {result['status']}")
        if asyncio.get_running_loop().time() > deadline:
            raise TimeoutError("Export still preparing")
        await asyncio.sleep(15)

    async with httpx.AsyncClient(timeout=60) as http:
        response = await http.get(result["downloadUrl"])
        response.raise_for_status()
    return pl.read_csv(io.BytesIO(response.content))


print(asyncio.run(export_gps(os.environ["SESSION_PARTICIPATION_ID"])))
```

The session mutation polls the same way and returns a zip. Read one athlete's file straight from it with `zipfile.ZipFile(path).open(f"{participation_id}/gps.csv")`.
