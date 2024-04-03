import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from common.constants import ENTRY_DATE_FORMAT
from webapp.api_v1.common_dependencies.schemas import UserMixinSchema


def validate_date(date: str) -> str:
    datetime.datetime.strptime(date, ENTRY_DATE_FORMAT)
    return date


FormattedDate = Annotated[str, AfterValidator(validate_date)]


class EntryBaseSchema(BaseModel):
    date: FormattedDate
    entry: str


class EntrySearchSchema(UserMixinSchema, BaseModel):
    date: FormattedDate


class EntrySaveSchema(EntryBaseSchema, UserMixinSchema):
    pass


class EntrySchema(EntryBaseSchema):
    id: int
    user_id: int


class ReportOrder(BaseModel):
    accepted_at: str
