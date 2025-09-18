import json
import threading
from pathlib import Path
from typing import Union

_lock = threading.Lock()
_offline_items: list[dict] = []


def add_offline(title: str, url: str, kind: str, reason: str = "") -> None:
    with _lock:
        _offline_items.append({
            "title": title,
            "url": url,
            "kind": kind,
            "reason": reason,
        })


def dump_offline_json(path: Union[Path, str]) -> int:
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    with _lock:
        data = list(_offline_items)
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Fallback ohne Pretty-Print
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return len(data)
