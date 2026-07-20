from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import HoursSummary, TimeEntryCreate, TimeEntryOut
from app.services import hours_service

router = APIRouter(prefix="/employees/{employee_id}/time-entries", tags=["time-entries"])


@router.post("/", response_model=TimeEntryOut)
def create_time_entry(employee_id: int, payload: TimeEntryCreate, db: Session = Depends(get_db)):
    entry = TimeEntry(employee_id=employee_id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[TimeEntryOut])
def list_time_entries(employee_id: int, db: Session = Depends(get_db)):
    return db.query(TimeEntry).filter(TimeEntry.employee_id == employee_id).all()


@router.get("/summary/week", response_model=HoursSummary)
def weekly_summary(employee_id: int, year: int, week: int, db: Session = Depends(get_db)):
    total = hours_service.get_hours_for_week(db, employee_id, year, week)
    return HoursSummary(period="week", period_label=f"{year}-W{week:02d}", total_hours=total)


@router.get("/summary/month", response_model=HoursSummary)
def monthly_summary(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be 1-12")
    total = hours_service.get_hours_for_month(db, employee_id, year, month)
    return HoursSummary(period="month", period_label=f"{year}-{month:02d}", total_hours=total)


@router.get("/summary/year", response_model=HoursSummary)
def yearly_summary(employee_id: int, year: int, db: Session = Depends(get_db)):
    total = hours_service.get_hours_for_year(db, employee_id, year)
    return HoursSummary(period="year", period_label=str(year), total_hours=total)
