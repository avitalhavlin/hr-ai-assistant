from datetime import date, datetime

from pydantic import BaseModel


class TimeEntryCreate(BaseModel):
    work_date: date
    start_time: datetime
    end_time: datetime | None = None


class TimeEntryUpdate(BaseModel):
    work_date: date | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class TimeEntryOut(BaseModel):
    id: int
    user_id: int
    work_date: date
    start_time: datetime
    end_time: datetime | None

    model_config = {"from_attributes": True}


class HoursSummary(BaseModel):
    period: str  # "week" | "month" | "year"
    period_label: str  # e.g. "2026-W29", "2026-07", "2026"
    total_hours: float
