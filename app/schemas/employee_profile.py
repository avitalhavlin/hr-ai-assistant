from datetime import date

from pydantic import BaseModel


class EmployeeProfileCreate(BaseModel):
    hire_date: date
    expected_daily_hours: float = 8.0
    remaining_vacation_days: float = 21.0


class EmployeeProfileOut(BaseModel):
    id: int
    user_id: int
    hire_date: date
    expected_daily_hours: float
    remaining_vacation_days: float

    model_config = {"from_attributes": True}
