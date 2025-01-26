import datetime as dt
import enum
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, as_declarative, deferred, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from src.core import exceptions
from src.core.settings import settings


@as_declarative()
class Base:
    """Базовая модель."""

    type_annotation_map = {
        uuid.UUID: UUID,
    }

    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=sa.func.current_timestamp(),
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=sa.func.current_timestamp(),
        onupdate=sa.func.current_timestamp(),
    )
    __name__: str


class Shift(Base):
    """Смена."""

    class Status(str, enum.Enum):
        """Статус смены."""

        STARTED = "started"
        FINISHED = "finished"
        READY_FOR_COMPLETE = "ready_for_complete"
        PREPARING = "preparing"
        CANCELLED = "cancelled"

    __tablename__ = "shifts"

    sequence_number: Mapped[int] = mapped_column(
        sa.Identity(
            start=1,
            cycle=True,
        ),
    )
    title: Mapped[str] = mapped_column(
        sa.String(60),
    )
    final_message: Mapped[str] = mapped_column(
        sa.String(400),
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(
            Status,
            name="shift_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    tasks: Mapped[sa.JSON] = mapped_column(type_=sa.JSON)

    started_at: Mapped[dt.date] = mapped_column(
        server_default=sa.func.current_timestamp(),  # TODO: Проверить необходимость значения по умолчанию
        index=True,
    )
    finished_at: Mapped[str] = mapped_column(
        index=True,
    )

    requests = relationship(
        "Request",
        back_populates="shift",
    )
    reports = relationship(
        "Report",
        back_populates="shift",
    )
    members = relationship(
        "Member",
        back_populates="shift",
        order_by="Member.member_user_name",
    )

    def __repr__(self) -> str:
        return f"<Shift: {self.id}, status: {self.status}>"

    async def start(self) -> None:
        if self.status != Shift.Status.PREPARING.value:
            raise exceptions.ShiftStartError(self)
        self.status = Shift.Status.STARTED.value
        self.started_at = dt.datetime.now().date()

    async def finish(self) -> None:
        if self.status != Shift.Status.STARTED.value:
            raise exceptions.ShiftFinishError(self)
        self.status = Shift.Status.FINISHED.value
        self.finished_at = dt.datetime.now().date()

    async def cancel(self, final_message: str) -> None:
        if self.status != Shift.Status.PREPARING.value:
            raise exceptions.ShiftCancelError(self)
        self.final_message = final_message
        self.status = Shift.Status.CANCELLED.value
        self.finished_at = dt.datetime.now().date()


class Task(Base):
    """Модель для описания задания."""

    __tablename__ = "tasks"

    sequence_number: Mapped[int] = mapped_column(
        sa.Identity(
            start=1,
            cycle=True,
        ),
    )
    title: Mapped[str] = mapped_column(
        sa.String(length=150),
        unique=True,
    )
    url: Mapped[str] = mapped_column(
        sa.String(length=150),
        unique=True,
    )
    is_archived: Mapped[bool] = mapped_column(
        default=False,
    )

    reports = relationship(
        "Report",
        back_populates="task",
    )

    def __repr__(self) -> str:
        return f"<Task: {self.id}, title: {self.title}>"


class User(Base):
    """Модель для пользователей."""

    class Status(str, enum.Enum):
        """Статус пользователя."""

        VERIFIED = "verified"
        DECLINED = "declined"
        PENDING = "pending"

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(
        sa.String(100),
    )
    surname: Mapped[str] = mapped_column(
        sa.String(100),
    )
    date_of_birth: Mapped[dt.date]
    city: Mapped[str] = mapped_column(
        sa.String(50),
    )
    phone_number: Mapped[str] = mapped_column(
        sa.String(16),
        unique=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        unique=True,
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(
            Status,
            name="user_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=Status.PENDING.value,
    )
    telegram_blocked: Mapped[bool] = mapped_column(
        default=False,
    )
    is_test_user: Mapped[bool] = mapped_column(
        default=False,
    )

    requests = relationship(
        "Request",
        back_populates="user",
    )
    members = relationship(
        "Member",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User: {self.id}, name: {self.name}, surname: {self.surname}>"


class Request(Base):
    """Модель рассмотрения заявок."""

    class Status(str, enum.Enum):
        """Статус рассмотрения заявки."""

        APPROVED = "approved"
        DECLINED = "declined"
        PENDING = "pending"

    __tablename__ = "requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            User.id,
            ondelete="CASCADE",
        ),
    )
    shift_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(Shift.id),
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(
            Status,
            name="request_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=Status.PENDING.value,
    )
    is_repeated: Mapped[int] = mapped_column(
        default=1,
    )

    shift = relationship(
        "Shift",
        back_populates="requests",
    )
    user = relationship(
        "User",
        back_populates="requests",
    )

    def __repr__(self) -> str:
        return f"<Request: {self.id}, status: {self.status}>"


class Member(Base):
    """Модель участников смены."""

    class Status(str, enum.Enum):
        """Статус участника смены."""

        ACTIVE = "active"
        EXCLUDED = "excluded"

    __tablename__ = "members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(User.id),
    )
    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Shift.id),
    )
    numbers_lombaryers: Mapped[int] = mapped_column(
        default=0,
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(
            Status,
            name="member_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=Status.ACTIVE.value,
    )
    member_user_name: Mapped[list[User]] = deferred(
        (sa.select(User.name).where(User.id == user_id)).scalar_subquery(),
    )

    shift = relationship(
        "Shift",
        back_populates="members",
    )
    user = relationship(
        "User",
        back_populates="members",
    )
    reports = relationship(
        "Report",
        back_populates="member",
        order_by="Report.task_date",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_id",
            "shift_id",
            name="_user_shift_uc",
        ),
    )

    def __repr__(self) -> str:
        return f"<Member: {self.id}, status: {self.status}>"


class Administrator(Base):
    """Модель администратора смены."""

    class Status(str, enum.Enum):
        """Статус администратора."""

        ACTIVE = "active"
        BLOCKED = "blocked"

    class Role(str, enum.Enum):
        """Роль администратора."""

        ADMINISTRATOR = "administrator"
        EXPERT = "expert"

    __tablename__ = "administrators"

    name: Mapped[str] = mapped_column(
        sa.String(100),
    )
    surname: Mapped[str] = mapped_column(
        sa.String(100),
    )
    email: Mapped[str] = mapped_column(
        sa.String(100),
        unique=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        sa.String(70),
    )
    role: Mapped[Role] = mapped_column(
        sa.Enum(
            Role,
            name="administrator_role",
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(
            Status,
            name="administrator_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    is_superadmin: Mapped[bool] = mapped_column(
        default=False,
    )
    last_login_at: Mapped[dt.datetime | None]

    reports = relationship(
        "Report",
        back_populates="reviewer",
    )

    def __repr__(self) -> str:
        return f"<Administrator: {self.name} {self.surname}, role: {self.role}>"


class Report(Base):
    """Ежедневные задания."""

    class Status(str, enum.Enum):
        """Статус задачи у пользователя."""

        REVIEWING = "reviewing"
        APPROVED = "approved"
        DECLINED = "declined"
        WAITING = "waiting"
        SKIPPED = "skipped"
        NOT_PARTICIPATE = "not_participate"

    __tablename__ = "reports"

    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Shift.id),
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Task.id),
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Member.id),
    )
    task_date: Mapped[dt.date]
    report_url: Mapped[str | None] = mapped_column(
        sa.String(length=4096),
        unique=True,
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(
            Status,
            name="report_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    number_attempt: Mapped[int] = mapped_column(
        server_default="0",
    )
    uploaded_at: Mapped[dt.datetime | None]
    reviewed_at: Mapped[dt.datetime | None]
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(Administrator.id),
    )

    shift = relationship(
        "Shift",
        back_populates="reports",
    )
    reviewer = relationship(
        "Administrator",
        back_populates="reports",
    )
    member = relationship(
        "Member",
        back_populates="reports",
    )
    task = relationship(
        "Task",
        back_populates="reports",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "shift_id",
            "task_date",
            "member_id",
            name="_member_task_uc",
        ),
    )

    def __repr__(self) -> str:
        return f"<Report: {self.id}, task_date: {self.task_date}, status: {self.status}>"

    def send_report(self, photo_url: str) -> None:
        if self.number_attempt == settings.NUMBER_ATTEMPTS_SUBMIT_REPORT:
            raise exceptions.ExceededAttemptsReportError
        if not photo_url:
            raise exceptions.EmptyReportError
        if self.status not in (
            Report.Status.WAITING.value,
            Report.Status.DECLINED.value,
        ):
            raise exceptions.CannotAcceptReportError
        self.status = Report.Status.REVIEWING.value
        self.report_url = photo_url
        self.uploaded_at = dt.datetime.now()
        self.number_attempt += 1

    def set_reviewer(self, administrator_id: uuid.UUID) -> None:
        """Установить администратора, который проверил отчет и дату проверки."""
        self.updated_by = administrator_id
        self.reviewed_at = dt.datetime.now()


class AdministratorInvitation(Base):
    """Модель приглашения администратора/психолога."""

    __tablename__ = "administrator_invitations"

    name: Mapped[str] = mapped_column(
        sa.String(100),
    )
    surname: Mapped[str] = mapped_column(
        sa.String(100),
    )
    email: Mapped[str] = mapped_column(
        sa.String(100),
    )
    token: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4,
    )
    expired_datetime: Mapped[dt.datetime]

    def __repr__(self) -> str:
        return f"<AdministratorInvitation: {self.id}, email: {self.email}, surname: {self.surname}, name: {self.name}>"
