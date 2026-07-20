from fastapi import FastAPI

from app.api import employees, health, time_entries, vacation_requests
from app.core.database import Base, engine

# Phase 0/1: create tables directly from models. Once Alembic is initialized
# in Phase 1, replace this with `alembic upgrade head` and remove this call.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HR AI Assistant",
    description="Time tracking + AI chatbot for employee hours, vacation, and policy questions.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(employees.router)
app.include_router(time_entries.router)
app.include_router(vacation_requests.router)

# app.include_router(chat.router)  # added in Phase 4
# app.include_router(admin.router)  # added in Phase 7
