import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from webapp.api_v1.common_dependencies.schemas import UserMixinSchema

DATE_FMT = "%d.%m.%y"


def validate_date(date: str) -> str:
    datetime.datetime.strptime(date, DATE_FMT)
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
