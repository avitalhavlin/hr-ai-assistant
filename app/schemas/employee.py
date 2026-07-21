from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from app.models.employee import Role


class EmployeeCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    hire_date: date
    role: Role = Role.employee
    expected_daily_hours: float = 8.0


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    expected_daily_hours: float
    hire_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
