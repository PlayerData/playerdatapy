from playerdatapy.custom_queries import Query
from playerdatapy.custom_fields import SessionParticipationInterface, EdgeDataFileFields
from playerdatapy.enums import DatafileFormat


def session_participations_urls(
    session_participation_ids: list[str],
) -> SessionParticipationInterface:
    return Query.session_participations(ids=session_participation_ids).fields(
        SessionParticipationInterface.id,
        SessionParticipationInterface.datafiles().fields(
            EdgeDataFileFields.url(format=DatafileFormat.json),
        ),
    )
