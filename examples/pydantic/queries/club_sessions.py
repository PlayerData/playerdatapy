from playerdatapy.custom_queries import Query
from playerdatapy.input_types import SessionsSessionFilter
from playerdatapy.custom_fields import SessionInterface


def club_sessions(club_id: str) -> SessionInterface:
    return Query.sessions(filter=SessionsSessionFilter(clubIdEq=club_id)).fields(
        SessionInterface.id, SessionInterface.start_time, SessionInterface.end_time
    )
