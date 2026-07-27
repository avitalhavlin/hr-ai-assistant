from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    expected_daily_hours: Mapped[float] = mapped_column(Float, default=8.0, server_default="8.0", nullable=False)
    hire_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    remaining_vacation_days: Mapped[float] = mapped_column(
        Float, default=21.0, server_default="21.0", nullable=False
    )

    user = relationship("User", back_populates="profile")
