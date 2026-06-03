import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

        with open("token.json", "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def create_event(service, shift):
    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

    event_body = shift_to_event_body(shift)

    created = (
        service.events()
        .insert(calendarId=calendar_id, body=event_body)
        .execute()
    )

    return created["id"]


def update_event(service, event_id, shift):
    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

    event_body = shift_to_event_body(shift)

    service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event_body,
    ).execute()


def delete_event(service, event_id):
    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

    service.events().delete(
        calendarId=calendar_id,
        eventId=event_id,
    ).execute()


def shift_to_event_body(shift):
    return {
        "summary": shift["title"],
        "location": shift.get("location", ""),
        "description": build_description(shift),
        "start": {
            "dateTime": shift["start"],
        },
        "end": {
            "dateTime": shift["end"],
        },
        "extendedProperties": {
            "private": {
                "wheniwork_shift_id": shift["id"],
                "managed_by": "wheniwork-google-calendar-sync",
            }
        },
    }


def build_description(shift):
    description = shift.get("description", "")

    return (
        f"{description}\n\n"
        f"Synced from When I Work.\n"
        f"When I Work Shift ID: {shift['id']}"
    ).strip()
