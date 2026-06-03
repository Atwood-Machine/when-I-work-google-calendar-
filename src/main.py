import hashlib
import json

from wheniwork import get_upcoming_shifts
from google_calendar import get_calendar_service, create_event, update_event, delete_event
from state import load_state, save_state


def fingerprint_shift(shift):
    important_parts = {
        "title": shift["title"],
        "start": shift["start"],
        "end": shift["end"],
        "location": shift.get("location", ""),
        "description": shift.get("description", ""),
    }

    raw = json.dumps(important_parts, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main():
    state = load_state()
    known_shifts = state.setdefault("shifts", {})

    service = get_calendar_service()
    shifts = get_upcoming_shifts()

    current_shift_ids = set()

    created_count = 0
    updated_count = 0
    deleted_count = 0
    unchanged_count = 0

    for shift in shifts:
        shift_id = shift["id"]
        current_shift_ids.add(shift_id)

        new_fingerprint = fingerprint_shift(shift)
        saved = known_shifts.get(shift_id)

        if not saved:
            event_id = create_event(service, shift)
            known_shifts[shift_id] = {
                "google_event_id": event_id,
                "fingerprint": new_fingerprint,
            }
            created_count += 1
            continue

        if saved["fingerprint"] != new_fingerprint:
            update_event(service, saved["google_event_id"], shift)
            saved["fingerprint"] = new_fingerprint
            updated_count += 1
        else:
            unchanged_count += 1

    for shift_id in list(known_shifts.keys()):
        if shift_id not in current_shift_ids:
            event_id = known_shifts[shift_id]["google_event_id"]

            try:
                delete_event(service, event_id)
            except Exception as error:
                print(f"Could not delete event for shift {shift_id}: {error}")

            del known_shifts[shift_id]
            deleted_count += 1

    save_state(state)

    print("Sync complete.")
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Deleted: {deleted_count}")
    print(f"Unchanged: {unchanged_count}")


if __name__ == "__main__":
    main()
