from datetime import datetime
from pydantic import BaseModel, Field, root_validator


class ShiftCreate(BaseModel):
    status: str = Field('preparing')
    started_at: datetime
    finished_at: datetime

    @root_validator
    def check_started_later_than_finished(cls, values):
        if values['started_at'] > values['finished_at']:
            raise ValueError(
                'Время начала смены '
                'не может быть больше конца'
            )
        return values
