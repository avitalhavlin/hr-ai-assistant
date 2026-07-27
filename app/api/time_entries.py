from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import HoursSummary, TimeEntryCreate, TimeEntryOut, TimeEntryUpdate
from app.services import hours_service, time_entry_service

router = APIRouter(prefix="/users/{user_id}/time-entries", tags=["time-entries"])


@router.post("/", response_model=TimeEntryOut)
def create_time_entry(user_id: int, payload: TimeEntryCreate, db: Session = Depends(get_db)):
    entry = TimeEntry(user_id=user_id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[TimeEntryOut])
def list_time_entries(user_id: int, db: Session = Depends(get_db)):
    return db.query(TimeEntry).filter(TimeEntry.user_id == user_id).all()


@router.patch("/{entry_id}", response_model=TimeEntryOut)
def update_time_entry(
    user_id: int, entry_id: int, payload: TimeEntryUpdate, db: Session = Depends(get_db)
):
    updates = payload.model_dump(exclude_unset=True)
    try:
        entry = time_entry_service.update_time_entry(db, user_id, entry_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry


@router.get("/summary/week", response_model=HoursSummary)
def weekly_summary(user_id: int, year: int, week: int, db: Session = Depends(get_db)):
    total = hours_service.get_hours_for_week(db, user_id, year, week)
    return HoursSummary(period="week", period_label=f"{year}-W{week:02d}", total_hours=total)


@router.get("/summary/month", response_model=HoursSummary)
def monthly_summary(user_id: int, year: int, month: int, db: Session = Depends(get_db)):
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be 1-12")
    total = hours_service.get_hours_for_month(db, user_id, year, month)
    return HoursSummary(period="month", period_label=f"{year}-{month:02d}", total_hours=total)


@router.get("/summary/year", response_model=HoursSummary)
def yearly_summary(user_id: int, year: int, db: Session = Depends(get_db)):
    total = hours_service.get_hours_for_year(db, user_id, year)
    return HoursSummary(period="year", period_label=str(year), total_hours=total)
