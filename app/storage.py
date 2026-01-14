import json
import time
from typing import Any
from .config import STATE_PATH, DEDUP_SECONDS


def _now() -> int:
    return int(time.time())


def load_state() -> dict[str, Any]:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"dedup": {}}


def save_state(state: dict[str, Any]) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def dedup_ok(key: str) -> bool:
    state = load_state()
    dedup = state.setdefault("dedup", {})

    last_ts = dedup.get(key)
    if last_ts and (_now() - last_ts) < DEDUP_SECONDS:
        return False

    dedup[key] = _now()
    save_state(state)
    return True
