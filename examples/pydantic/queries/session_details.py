from playerdatapy.custom_queries import Query
from playerdatapy.custom_fields import (
    SessionInterface,
    SessionParticipationInterface,
    AthleteFields,
    SegmentParticipationFields,
    SegmentFields,
)


def session_details(session_id: str):
    return Query.session(id=session_id).fields(
        SessionInterface.session_participations().fields(
            SessionParticipationInterface.id,
            SessionParticipationInterface.athlete().fields(
                AthleteFields.id,
                AthleteFields.name,
            ),
            SessionParticipationInterface.segment_participations().fields(
                SegmentParticipationFields.segment().fields(
                    SegmentFields.title,
                    SegmentFields.start_time,
                    SegmentFields.end_time,
                ),
            ),
        ),
    )
