from playerdatapy.custom_fields import (
    RequestRawDataExportPayloadFields,
    ValidationErrorFields,
)
from playerdatapy.custom_mutations import Mutation
from playerdatapy.enums import RawDataExportFormatEnum, RawDataExportTypeEnum


def request_raw_data_export(
    session_participation_id: str,
    data_type: RawDataExportTypeEnum = RawDataExportTypeEnum.GPS,
    format: RawDataExportFormatEnum = RawDataExportFormatEnum.CSV,
) -> RequestRawDataExportPayloadFields:
    return Mutation.request_raw_data_export(
        session_participation_id=session_participation_id,
        data_type=data_type,
        format=format,
    ).fields(
        RequestRawDataExportPayloadFields.status,
        RequestRawDataExportPayloadFields.download_url,
        RequestRawDataExportPayloadFields.errors().fields(
            ValidationErrorFields.full_messages
        ),
    )
