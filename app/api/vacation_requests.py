from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.employee import Employee, Role
from app.schemas.vacation_request import VacationRequestCreate, VacationRequestOut
from app.services import vacation_service

router = APIRouter(tags=["vacation-requests"])

# NOTE: real JWT-based auth lands in Phase 3. Until then, admin-only actions
# are gated by an X-Admin-Employee-Id header identifying the acting employee,
# which must resolve to an employee with the admin role. Replace this
# dependency with a proper get_current_employee()-based check in Phase 3.


def require_admin(
    x_admin_employee_id: int = Header(..., alias="X-Admin-Employee-Id"),
    db: Session = Depends(get_db),
) -> Employee:
    admin = db.get(Employee, x_admin_employee_id)
    if admin is None:
        raise HTTPException(status_code=401, detail="Unknown acting employee")
    if admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return admin


@router.post(
    "/employees/{employee_id}/vacation-requests/",
    response_model=VacationRequestOut,
)
def create_vacation_request(
    employee_id: int, payload: VacationRequestCreate, db: Session = Depends(get_db)
):
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    try:
        return vacation_service.create_vacation_request(
            db, employee_id, payload.start_date, payload.end_date
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/employees/{employee_id}/vacation-requests/",
    response_model=list[VacationRequestOut],
)
def list_vacation_requests(employee_id: int, db: Session = Depends(get_db)):
    return vacation_service.list_vacation_requests(db, employee_id)


@router.post("/vacation-requests/{request_id}/approve", response_model=VacationRequestOut)
def approve_vacation_request(
    request_id: int,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(require_admin),
):
    try:
        return vacation_service.approve_vacation_request(db, request_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/vacation-requests/{request_id}/reject", response_model=VacationRequestOut)
def reject_vacation_request(
    request_id: int,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(require_admin),
):
    try:
        return vacation_service.reject_vacation_request(db, request_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
