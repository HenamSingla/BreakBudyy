from fastapi import FastAPI, Query
from typing import List, Dict
from datetime import date, timedelta

app = FastAPI(title="SmartPTO API", version="0.1.0")

# --- Fake in-memory data store ---
EMPLOYEES: Dict[str, Dict] = {
    "u1": {"id": "u1", "name": "Ryan", "accrual_days": 8.5, "team": "alpha"},
    "u2": {"id": "u2", "name": "Alex", "accrual_days": 12, "team": "alpha"},
    "u3": {"id": "u3", "name": "Priya", "accrual_days": 6, "team": "beta"},
}
TEAM_OUT: Dict[str, List[str]] = {
    "alpha": ["2025-10-20", "2025-10-21"],
    "beta": ["2025-10-15"],
}

# --- Healthcheck ---
@app.get("/health")
def health():
    return {"status": "ok"}


# --- Balance ---
@app.get("/balance")
def balance(employee_id: str = Query(..., description="Employee ID to check balance")):
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        return {"error": "employee not found", "employee_id": employee_id}
    return {
        "employee_id": emp["id"],
        "name": emp["name"],
        "accrual_days": emp["accrual_days"],
    }


# --- Recommend ---
@app.get("/recommend")
def recommend(
    employee_id: str = Query(...),
    desired_len_days: int = Query(3, ge=1, le=14),
):
    """Suggest a PTO window (dummy implementation)."""
    if employee_id not in EMPLOYEES:
        return {"error": "employee not found", "employee_id": employee_id}

    today = date.today()
    start = today + timedelta(days=7)  # pretend we always recommend 1 week from today
    end = start + timedelta(days=desired_len_days - 1)

    return [
        {
            "employee_id": employee_id,
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "reason": "Demo rule: always suggest next week",
            "coverage_ratio": 0.1,
        }
    ]











# --- Gmail endpoints (demo stubs) ---
@app.get("/gmail/holiday-suggestions")
def gmail_suggestions(max_results: int = 20):
    # Return fake keyword matches
    return {
        "items": [
            {"subject": "Holiday trip to Japan", "from": "travel@airline.com", "date": "2025-09-01"},
            {"subject": "OOO notice", "from": "colleague@company.com", "date": "2025-09-15"}
        ]
    }

@app.get("/gmail/analyze")
def gmail_analyze(max_results: int = 50):
    # Return fake AI suggestions
    return {
        "count_messages": max_results,
        "suggestions": [
            {
                "window_start": "2025-12-20",
                "window_end": "2025-12-27",
                "reason": "Detected email about Japan trip during holidays",
                "confidence": 0.92,
                "source_message_id": "msg123"
            }
        ]
    }

