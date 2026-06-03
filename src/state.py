import json
from pathlib import Path

STATE_FILE = Path("sync_state.json")


def load_state():
    if not STATE_FILE.exists():
        return {"shifts": {}}

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, sort_keys=True)
