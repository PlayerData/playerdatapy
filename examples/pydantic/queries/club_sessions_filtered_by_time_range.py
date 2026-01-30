from playerdatapy.custom_queries import Query
from playerdatapy.input_types import SessionsSessionFilter
from playerdatapy.custom_fields import SessionInterface
from datetime import datetime


def club_sessions_filtered_by_time_range(
    club_id: str, start_time_gteq: datetime, end_time_lteq: datetime = datetime.now()
) -> SessionInterface:
    return Query.sessions(
        filter=SessionsSessionFilter(
            clubIdEq=club_id, startTimeGteq=start_time_gteq, endTimeLteq=end_time_lteq
        )
    ).fields(
        SessionInterface.id, SessionInterface.start_time, SessionInterface.end_time
    )
