from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import Role


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Role = Role.employee


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None


class UserRoleUpdate(BaseModel):
    role: Role


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    created_at: datetime

    model_config = {"from_attributes": True}
