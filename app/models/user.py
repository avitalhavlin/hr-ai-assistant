import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Role(str, enum.Enum):
    employee = "employee"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.employee, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    time_entries = relationship("TimeEntry", back_populates="user", cascade="all, delete-orphan")
    profile = relationship(
        "EmployeeProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
