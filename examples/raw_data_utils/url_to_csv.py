import polars as pl
import httpx
import os


def raw_gps_data(json_data: list[dict]) -> pl.DataFrame:
    """
    Extracts GPS data from JSON data and returns a DataFrame.

    Args:
        json_data: List of dictionaries containing the raw data.

    Returns:
        A DataFrame containing the GPS data.
    """
    schema = {
        "time": pl.Int64,
        "latitude": pl.Float32,
        "longitude": pl.Float32,
        "speed": pl.Float32,
        "satellites": pl.UInt8,
        "type": pl.String,
    }
    participation_data = pl.DataFrame(json_data, schema=schema)
    gps_events = participation_data.filter(pl.col("type") == "GPS")

    if gps_events.is_empty():
        return pl.DataFrame()

    gps_data = gps_events.select(
        [
            pl.from_epoch(pl.col("time"), time_unit="ms").dt.replace_time_zone("UTC"),
            pl.col("latitude").cast(pl.Float32),
            pl.col("longitude").cast(pl.Float32),
            pl.col("speed").cast(pl.Float32),
            pl.col("satellites").cast(pl.UInt8),
        ]
    ).sort("time")

    return gps_data


def raw_imu_acceleration_data(json_data: list[dict]) -> pl.DataFrame:
    """
    Extracts IMU acceleration data from JSON data and returns a DataFrame.

    Args:
        json_data: List of dictionaries containing the raw data.

    Returns:
        A DataFrame containing the IMU acceleration data.
    """
    schema = {
        "time": pl.Int64,
        "x": pl.Float32,
        "y": pl.Float32,
        "z": pl.Float32,
        "type": pl.String,
    }
    participation_data = pl.DataFrame(json_data, schema=schema)
    acceleration_events = participation_data.filter(pl.col("type") == "ACCELERATION")

    if acceleration_events.is_empty():
        return pl.DataFrame()

    acceleration_data = acceleration_events.select(
        [
            pl.from_epoch(pl.col("time"), time_unit="ms").dt.replace_time_zone("UTC"),
            pl.col(["x", "y", "z"]).cast(pl.Float32),
        ]
    ).sort("time")

    return acceleration_data


def raw_imu_orientation_data(json_data: list[dict]) -> pl.DataFrame:
    """
    Extracts IMU orientation data from JSON data and returns a DataFrame.

    Args:
        json_data: List of dictionaries containing the raw data.

    Returns:
        A DataFrame containing the IMU orientation data.
    """
    schema = {
        "time": pl.Int64,
        "x": pl.Float32,
        "y": pl.Float32,
        "z": pl.Float32,
        "w": pl.Float32,
        "type": pl.String,
    }
    participation_data = pl.DataFrame(json_data, schema=schema)
    orientation_events = participation_data.filter(
        pl.col("type") == "DEVICE_ORIENTATION"
    )

    if orientation_events.is_empty():
        return pl.DataFrame()

    orientation_data = orientation_events.select(
        [
            pl.from_epoch(pl.col("time"), time_unit="ms").dt.replace_time_zone("UTC"),
            pl.col(["x", "y", "z", "w"]).cast(pl.Float32),
        ]
    ).sort("time")

    return orientation_data


def url_to_csv(url: str, session_participation_id: str) -> None:
    """
    Fetches JSON data from a URL, extracts GPS and IMU data, and writes to CSV files
    in a dedicated folder named after the session_participation_id.

    Args:
        url: URL to fetch JSON data from.
        session_participation_id: ID used to name and organize output directory/files.
    """
    # Fetch JSON data from URL
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        json_data = response.json()

    # Extract GPS, IMU acceleration, and IMU orientation data
    gps_data = raw_gps_data(json_data)
    imu_acceleration_data = raw_imu_acceleration_data(json_data)
    imu_orientation_data = raw_imu_orientation_data(json_data)

    # Create a directory for this session_participation_id if it doesn't exist
    output_dir = session_participation_id
    os.makedirs(output_dir, exist_ok=True)

    # Write data to CSV files inside the new directory
    gps_data.write_csv(
        os.path.join(output_dir, f"gps_data_{session_participation_id}.csv"),
        separator=",",
    )
    imu_acceleration_data.write_csv(
        os.path.join(
            output_dir, f"imu_acceleration_data_{session_participation_id}.csv"
        ),
        separator=",",
    )
    imu_orientation_data.write_csv(
        os.path.join(
            output_dir, f"imu_orientation_data_{session_participation_id}.csv"
        ),
        separator=",",
    )
