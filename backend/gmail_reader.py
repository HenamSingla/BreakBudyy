


# backend/gmail_reader.py
from __future__ import annotations
import re
import json
from email.utils import parsedate_to_datetime
from typing import List, Dict, Any, Tuple
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If you installed google-generativeai and configured GEMINI key, we'll call it
try:
    import google.generativeai as genai
except Exception:
    genai = None

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "backend/credentials.json"
TOKEN_FILE = "backend/token.json"
MODEL = "gemini-1.5-flash"

# ---------------- Gmail auth / service ----------------
def _get_service():
    creds = None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except Exception:
        creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def _get_full_message(service, msg_id: str) -> Dict[str, Any]:
    # returns dict with headers and a plain-text body (best effort)
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    # extract plain text from payload (walk)
    body = ""
    def _walk_parts(p):
        nonlocal body
        if p is None:
            return
        mime = p.get("mimeType", "")
        if mime == "text/plain" and "data" in (p.get("body") or {}):
            import base64
            data = p["body"]["data"]
            body += base64.urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
        for part in p.get("parts", []) or []:
            _walk_parts(part)

    _walk_parts(msg.get("payload"))
    return {"id": msg_id, "headers": headers, "body": body, "snippet": msg.get("snippet", "")}

# -------------- rule based date extraction (fallback) --------------
# Simple regexes for common date phrases (very approximate)
DATE_PATTERNS = [
    r"\b(?:on\s)?(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}\b",
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b(?:next|this|coming)\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    r"\b(?:in\s)?(\d{1,2})\s+days\b",
    r"\b(?:from)\s+(?P<start>.+?)\s+(?:to|-|through)\s+(?P<end>.+?)\b",
    r"\b(?:going to|go to|trip to|travel to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",  # location
]

def find_date_strings(text: str) -> List[str]:
    found = []
    for pat in DATE_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            found.append(m.group(0))
    return list(dict.fromkeys(found))  # dedupe preserve order

# convert some strings to a candidate start/end date (best-effort)
def normalize_date_string(s: str, ref: datetime) -> Tuple[datetime | None, datetime | None]:
    s = s.strip()
    # try common simple formats
    try:
        # try mm/dd or mm/dd/yyyy
        from dateutil import parser
        dt = parser.parse(s, default=ref)
        return dt.date(), dt.date()
    except Exception:
        pass
    # naive "in N days"
    m = re.search(r"(\d{1,2})\s+days", s, flags=re.IGNORECASE)
    if m:
        days = int(m.group(1))
        start = ref.date() + timedelta(days=days)
        return start, start
    return None, None

# -------------- Gemini / LLM wrapper --------------
def _setup_gemini():
    key = None
    if genai is None:
        return False
    # look for env var
    import os
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return False
    genai.configure(api_key=key)
    return True

def analyze_with_gemini(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ask Gemini to scan the messages and return structured suggested PTO windows.
    We prompt it to return JSON like:
    [{ "window_start": "YYYY-MM-DD", "window_end": "YYYY-MM-DD", "reason": "...", "source": "<msg_id>", "confidence": 0.8 }, ...]
    """
    if not _setup_gemini():
        return []

    # Build a compact prompt with messages (trim long bodies)
    snippets = []
    for m in messages:
        body = m.get("body") or m.get("snippet") or ""
        if len(body) > 1500:
            body = body[:1500] + " ...[truncated]"
        snippets.append({"id": m["id"], "from": m["headers"].get("from",""), "subject": m["headers"].get("subject",""), "body": body})

    prompt_text = (
        "You are an assistant that scans email content and finds potential requests or signals "
        "that would justify suggesting PTO windows for the user. For each message, look for travel plans, event dates, interviews, or explicit time-off requests. "
        "Return a JSON array of suggestions. Each suggestion should include keys: "
        '"window_start" (ISO date), "window_end" (ISO date), "reason" (short text), "source_message_id", and "confidence" (0.0-1.0). '
        "If no suggestion for a message, do not include it. Be conservative; only propose windows that are clearly implied.\n\n"
        "Messages:\n"
    )
    for s in snippets:
        prompt_text += f"---\nid: {s['id']}\nfrom: {s['from']}\nsubject: {s['subject']}\nbody: {s['body']}\n\n"

    model = genai.GenerativeModel(MODEL)
    res = model.generate_content(prompt_text)
    raw = res.text if hasattr(res, "text") else getattr(res, "output", str(res))
    # try parse JSON
    try:
        data = json.loads(raw)
        return data
    except Exception:
        # if model returned text, attempt to find a JSON block
        jmatch = re.search(r"(\[.*\])", raw, flags=re.S)
        if jmatch:
            try:
                return json.loads(jmatch.group(1))
            except Exception:
                pass
    return []

# -------------- Public endpoint helper --------------
from datetime import timedelta, datetime
def scan_and_suggest(max_results: int = 50) -> Dict[str, Any]:
    service = _get_service()
    # search for messages with likely keywords (broad)
    q = 'subject:(holiday OR PTO OR "out of office" OR OOO OR trip OR travel OR vacation) OR (body:(vacation OR "going to" OR "travel to" OR "trip to" OR "time off")) newer_than:365d'
    resp = service.users().messages().list(userId="me", q=q, maxResults=max_results).execute()
    messages = resp.get("messages", [])
    fulls = []
    for m in messages:
        fulls.append(_get_full_message(service, m["id"]))

    # Try LLM analysis first
    suggestions = []
    if genai is not None and _setup_gemini():
        try:
            suggestions = analyze_with_gemini(fulls)
        except Exception as e:
            suggestions = []

    # Fallback: naive rule-based extractor
    if not suggestions:
        now = datetime.now()
        for fm in fulls:
            text = (fm.get("body") or "") + " " + (fm.get("headers", {}).get("subject","") or "")
            date_strs = find_date_strings(text)
            if date_strs:
                for ds in date_strs:
                    start, end = normalize_date_string(ds, now)
                    if start:
                        suggestions.append({
                            "window_start": start.isoformat(),
                            "window_end": end.isoformat() if end else start.isoformat(),
                            "reason": f"Found phrase `{ds}` in message subject/body",
                            "source_message_id": fm["id"],
                            "confidence": 0.4
                        })
            # also detect travel to Japan or other location words
            if re.search(r"\b(japan|tokyo|travel to japan|going to japan|trip to japan)\b", text, flags=re.IGNORECASE):
                # suggest a 7-day window starting ~30 days from now as an example
                s = (now + timedelta(days=30)).date()
                suggestions.append({
                    "window_start": s.isoformat(),
                    "window_end": (s + timedelta(days=6)).isoformat(),
                    "reason": "Travel mention: Japan found in message",
                    "source_message_id": fm["id"],
                    "confidence": 0.6
                })

    return {"count_messages": len(fulls), "suggestions": suggestions}
