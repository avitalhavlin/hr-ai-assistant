from datetime import date

from pydantic import BaseModel

from app.models.vacation_request import VacationStatus


class VacationRequestCreate(BaseModel):
    start_date: date
    end_date: date


class VacationRequestUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class VacationRequestOut(BaseModel):
    id: int
    user_id: int
    start_date: date
    end_date: date
    status: VacationStatus

    model_config = {"from_attributes": True}
