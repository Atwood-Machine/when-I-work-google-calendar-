import os
import requests
from datetime import datetime, timedelta, timezone


LOGIN_URL = "https://api.login.wheniwork.com/login"
BASE_URL = "https://api.wheniwork.com/2"


def get_wiw_token():
    developer_key = os.environ["WIW_DEVELOPER_KEY"]
    email = os.environ["WIW_EMAIL"]
    password = os.environ["WIW_PASSWORD"]

    response = requests.post(
        LOGIN_URL,
        headers={
            "W-Key": developer_key,
            "content-type": "application/json",
        },
        json={
            "email": email,
            "password": password,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    token = (
        data.get("token")
        or data.get("person", {}).get("token")
        or data.get("user", {}).get("token")
    )

    if not token:
        raise RuntimeError(f"Could not find token in When I Work login response: {data}")

    return token


def get_upcoming_shifts():
    token = get_wiw_token()
    user_id = os.environ["WIW_USER_ID"]

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=60)

    headers = {
        "Authorization": f"Bearer {token}",
        "W-UserId": str(user_id),
        "Accept": "application/json",
    }

    params = {
        "start": start.date().isoformat(),
        "end": end.date().isoformat(),
    }

    response = requests.get(
        f"{BASE_URL}/shifts",
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    shifts = data.get("shifts", data if isinstance(data, list) else [])

    normalized = []
    for shift in shifts:
        normalized.append(normalize_shift(shift))

    return normalized


def normalize_shift(shift):
    shift_id = str(shift.get("id"))

    start_time = (
        shift.get("start_time")
        or shift.get("start")
        or shift.get("starts_at")
    )

    end_time = (
        shift.get("end_time")
        or shift.get("end")
        or shift.get("ends_at")
    )

    position = shift.get("position_name") or shift.get("position") or "Shift"
    location = shift.get("location_name") or shift.get("location") or ""
    notes = shift.get("notes") or ""

    if not shift_id or not start_time or not end_time:
        raise ValueError(f"Shift is missing required fields: {shift}")

    return {
        "id": shift_id,
        "title": f"Work: {position}",
        "start": start_time,
        "end": end_time,
        "location": location,
        "description": notes,
        "raw": shift,
    }
