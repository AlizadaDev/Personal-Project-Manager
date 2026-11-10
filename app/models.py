"""ORM models: Project, Task, Note."""

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import ProjectCategory, ProjectStatus, TaskPriority, TaskStatus


def text_enum(enum_cls: type[StrEnum]) -> Enum:
    """Store an enum as its readable value (e.g. "In Progress"), not its Python name."""
    return Enum(
        enum_cls,
        values_callable=lambda members: [m.value for m in members],
        native_enum=False,
        length=30,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[ProjectCategory] = mapped_column(
        text_enum(ProjectCategory), default=ProjectCategory.OTHER
    )
    status: Mapped[ProjectStatus] = mapped_column(
        text_enum(ProjectStatus), default=ProjectStatus.PLANNING, index=True
    )
    start_date: Mapped[date | None]
    deadline: Mapped[date | None]

    # Deleting a project deletes its tasks (DB-level CASCADE) but keeps its notes (SET NULL).
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    notes: Mapped[list["Note"]] = relationship(back_populates="project", passive_deletes=True)

    @property
    def is_overdue(self) -> bool:
        return (
            self.deadline is not None
            and self.status != ProjectStatus.COMPLETED
            and self.deadline < date.today()
        )


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        text_enum(TaskPriority), default=TaskPriority.MEDIUM
    )
    status: Mapped[TaskStatus] = mapped_column(
        text_enum(TaskStatus), default=TaskStatus.TODO, index=True
    )
    due_date: Mapped[date | None] = mapped_column(index=True)
    completed_at: Mapped[datetime | None]

    project: Mapped[Project | None] = relationship(back_populates="tasks")

    @property
    def is_done(self) -> bool:
        return self.status == TaskStatus.DONE

    @property
    def is_overdue(self) -> bool:
        return self.due_date is not None and not self.is_done and self.due_date < date.today()


class Note(TimestampMixin, Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )

    project: Mapped[Project | None] = relationship(back_populates="notes")
