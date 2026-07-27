from datetime import date

from pydantic import BaseModel


class EmployeeProfileOut(BaseModel):
    id: int
    user_id: int
    hire_date: date
    expected_daily_hours: float
    remaining_vacation_days: float

    model_config = {"from_attributes": True}
