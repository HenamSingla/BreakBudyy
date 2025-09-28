# backend/gemini.py
import os, json
import google.generativeai as genai

MODEL = "gemini-1.5-flash"

def _setup() -> bool:
    key = "AIzaSyDfJTT90L-zbc1MQAovGikuDpj0ce5CZGE"   # <--- paste directly
    if not key:
        return False
    genai.configure(api_key=key)
    return True


def pick_best_window(employee, candidates, desired_len_days, horizon_days):
    """
    candidates: list of {window_start, window_end, coverage_ratio}
    returns {window_start, window_end, reason, ai_model} or None
    """
    if not _setup() or not candidates:
        return None
    system = (
        "Select the best PTO window from the candidates. "
        "Prefer lower coverage_ratio and earlier dates. "
        "Return STRICT JSON with keys: window_start, window_end, reason."
    )
    payload = {
        "employee": {
            "id": employee["id"], "name": employee["name"],
            "team": employee.get("team"), "accrual_days": employee["accrual_days"]
        },
        "constraints": {"desired_len_days": desired_len_days, "horizon_days": horizon_days},
        "candidates": candidates
    }
    text = genai.GenerativeModel(MODEL).generate_content(
        f"{system}\nRespond ONLY with JSON.\n{json.dumps(payload)}"
    ).text.strip()

    if text.startswith("```"):
        # strip code fences / leading "json"
        lines = [ln for ln in text.strip("`").splitlines() if ln.strip().lower() != "json"]
        text = "\n".join(lines)

    data = json.loads(text)
    return {
        "window_start": data["window_start"],
        "window_end": data["window_end"],
        "reason": data["reason"],
        "ai_model": MODEL,
    }

def summarize_pto_request(employee_name: str, days: int, reason: str = "") -> str:
    """
    Simple text summary so /ai_recommend works.
    If no key is set, return a graceful message instead of crashing.
    """
    if not _setup():
        return f"(No AI key configured) Suggested {days} day(s) off for {employee_name}."

    prompt = (
        f"Employee {employee_name} wants to take {days} day(s) off. "
        f"{'Reason: ' + reason if reason else ''} "
        "Write a kind, brief note to their manager explaining that coverage looks reasonable."
    )
    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    return (resp.text or "").strip()
