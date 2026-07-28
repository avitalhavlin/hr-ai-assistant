from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmployeeProfile(Base):
    """One-to-one HR data for a User. Created and deleted alongside its User
    (see app/api/users.py) so the two rows always exist or don't exist together;
    fields with no sensible default are nullable and can be filled in later."""

    __tablename__ = "employee_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    expected_daily_hours: Mapped[float] = mapped_column(Float, default=8.0, server_default="8.0", nullable=False)
    hire_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remaining_vacation_days: Mapped[float] = mapped_column(
        Float, default=21.0, server_default="21.0", nullable=False
    )

    user = relationship("User", back_populates="profile")
