from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role = Role.employee
    hire_date: Optional[date] = None
    expected_daily_hours: float = 8.0
    remaining_vacation_days: float = 21.0


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithProfileOut(UserOut):
    hire_date: Optional[date]
    expected_daily_hours: float
    remaining_vacation_days: float
