from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class Employee(BaseModel):
    id: str
    name: str
    team: str
    manager_id: Optional[str] = None
    accrual_days: float  # current available PTO days


class PTORequest(BaseModel):
    employee_id: str
    start_date: date
    end_date: date
    status: str  # pending/approved/denied


class PTORecommendation(BaseModel):
    employee_id: str
    window_start: date
    window_end: date
    reason: str
    coverage_ratio: float  # fraction of team out on those days
