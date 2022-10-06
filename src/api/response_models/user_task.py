from pydantic import BaseModel
from pydantic.schema import UUID

from src.api.response_models.shift import ShiftResponse
from src.api.response_models.task import TaskInfoResponse
from src.api.response_models.user import UserInfoResponse
from src.core.db.models import UserTask


class UserAndTaskInfoResponse(UserInfoResponse, TaskInfoResponse):
    """Модель для ответа c обобщенной информацией о задании и юзере."""

    id: UUID


class UserTasksAndShiftResponse(BaseModel):
    """Общая модель смены и заданий для ответа."""

    shift: ShiftResponse
    tasks: list[UserAndTaskInfoResponse]


class UserTaskResponse(BaseModel):
    """Pydantic-схема, для описания объекта, полученного из БД."""

    user_id: UUID
    user_task_id: UUID
    task_id: UUID
    day_number: int
    status: UserTask.Status
    photo_url: str

    class Config:
        orm_mode = True