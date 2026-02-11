from playerdatapy.custom_queries import Query
from playerdatapy.custom_fields import (
    SessionInterface,
    BallDataRecordingFields,
    BallFields,
)
from playerdatapy.enums import DatafileFormat


def session_ball_data(session_id: str):
    """Session by id with ball data recordings (id, url as JSON, ball id and serial number)."""
    return Query.session(id=session_id).fields(
        SessionInterface.id,
        SessionInterface.start_time,
        SessionInterface.end_time,
        SessionInterface.ball_data_recordings().fields(
            BallDataRecordingFields.id,
            BallDataRecordingFields.url(format=DatafileFormat.json),
            BallDataRecordingFields.ball().fields(
                BallFields.id,
                BallFields.serial_number,
            ),
        ),
    )
