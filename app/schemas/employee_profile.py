from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class EmployeeProfileOut(BaseModel):
    id: int
    user_id: int
    hire_date: Optional[date]
    expected_daily_hours: float
    remaining_vacation_days: float

    model_config = {"from_attributes": True}


class EmployeeProfileUpdate(BaseModel):
    hire_date: Optional[date] = None
    # expected_daily_hours/remaining_vacation_days stay Optional so the field
    # can be omitted from a partial update, but the DB columns are NOT NULL,
    # so an explicit null must be rejected rather than passed through.
    expected_daily_hours: Optional[float] = None
    remaining_vacation_days: Optional[float] = None

    @field_validator("expected_daily_hours", "remaining_vacation_days")
    @classmethod
    def _reject_null(cls, value: Optional[float]) -> float:
        if value is None:
            raise ValueError("must not be null")
        return value
