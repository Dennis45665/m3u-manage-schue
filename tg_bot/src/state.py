import json
from pathlib import Path
from typing import Dict, Optional

# Änderung: Neue State-/Snapshot-Hilfen zum Speichern/Laden des letzten
# Jellyfin-Zustands, um echte Diffs zwischen Läufen zu ermöglichen.
BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "tmp"
SNAPSHOT_FILE = TMP_DIR / "jellyfin_snapshot.json"


def ensure_tmp_dir():
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def load_snapshot() -> Optional[Dict]:
    """Lädt den letzten Snapshot, falls vorhanden (sonst None)."""
    ensure_tmp_dir()
    if not SNAPSHOT_FILE.exists():
        return None
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def save_snapshot(data: Dict) -> None:
    """Speichert den aktuellen Snapshot als JSON."""
    ensure_tmp_dir()
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _index_by_id(items):
    return {item.get("Id"): item for item in items if item and item.get("Id")}


def compute_new_items(prev: Dict, current: Dict) -> Dict:
    """
    Vergleicht vorherigen und aktuellen Snapshot und liefert neue Elemente pro Typ
    (movies, series, episodes). Änderung: Live-TV bewusst außen vor gelassen.
    """
    new_data = {}
    for key in ("movies", "series", "episodes"):
        prev_items = prev.get(key, []) if prev else []
        curr_items = current.get(key, []) if current else []
        prev_index = _index_by_id(prev_items)
        additions = [it for it in curr_items if it.get("Id") not in prev_index]
        if additions:
            new_data[key] = additions
    return new_data
