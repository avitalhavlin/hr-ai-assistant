from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.time_entry import HoursSummary, TimeEntryCreate, TimeEntryOut
from app.services import hours_service, time_entry_service

router = APIRouter(prefix="/users/{user_id}/time-entries", tags=["time-entries"])


@router.post("/", response_model=TimeEntryOut)
def create_time_entry(user_id: int, payload: TimeEntryCreate, db: Session = Depends(get_db)):
    try:
        return time_entry_service.create_time_entry(db, user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=list[TimeEntryOut])
def list_time_entries(user_id: int, db: Session = Depends(get_db)):
    return time_entry_service.list_time_entries(db, user_id)


@router.get("/summary/week", response_model=HoursSummary)
def weekly_summary(user_id: int, year: int, week: int, db: Session = Depends(get_db)):
    try:
        total = hours_service.get_hours_for_week(db, user_id, year, week)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return HoursSummary(period="week", period_label=f"{year}-W{week:02d}", total_hours=total)


@router.get("/summary/month", response_model=HoursSummary)
def monthly_summary(user_id: int, year: int, month: int, db: Session = Depends(get_db)):
    try:
        total = hours_service.get_hours_for_month(db, user_id, year, month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return HoursSummary(period="month", period_label=f"{year}-{month:02d}", total_hours=total)


@router.get("/summary/year", response_model=HoursSummary)
def yearly_summary(user_id: int, year: int, db: Session = Depends(get_db)):
    total = hours_service.get_hours_for_year(db, user_id, year)
    return HoursSummary(period="year", period_label=str(year), total_hours=total)
