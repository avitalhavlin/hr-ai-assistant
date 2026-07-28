from datetime import date
from typing import Optional

from pydantic import BaseModel


class EmployeeProfileOut(BaseModel):
    id: int
    user_id: int
    hire_date: Optional[date]
    expected_daily_hours: float
    remaining_vacation_days: float

    model_config = {"from_attributes": True}


class EmployeeProfileUpdate(BaseModel):
    hire_date: Optional[date] = None
    expected_daily_hours: Optional[float] = None
    remaining_vacation_days: Optional[float] = None
