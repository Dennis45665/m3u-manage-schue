import requests
from ..logger import tg_logger
import json

def get_jellyfin_data(jellyfin_url, jellyfin_api_key):
    """
    Änderung: Kein Zeitfenster mehr. Es werden alle Items geladen und mit dem
    vorherigen Snapshot verglichen. Zusätzliche Felder (SeriesId, etc.) für
    korrekte Zuordnung und spätere Gruppierung wurden ergänzt.
    """
    tg_logger.info("Hole & Erstelle Jellyfin Data (ohne Zeitfenster)")

    headers = {
        "X-Emby-Token": jellyfin_api_key
    }

    base_items_url = f"{jellyfin_url}/emby/Items"
    item_params = {
        "IncludeItemTypes": "Series,Movie,Episode",
        "Recursive": "true",
        # Änderung: Zusatzfelder erweitert, damit Serien/Episoden korrekt
        # zugeordnet und gruppiert werden können (SeriesId u.a.).
        "Fields": "DateCreated,Path,SeriesName,SeriesId,SeasonName,IndexNumber,ParentIndexNumber,ProductionYear,Overview",
        "SortBy": "DateCreated",
        "SortOrder": "Descending",
    }

    try:
        r = requests.get(base_items_url, headers=headers, params=item_params)
        r.raise_for_status()
        items = r.json().get("Items", [])
        tg_logger.info(f"Jellyfin API response: {json.dumps(items, indent=2)}")
    except Exception as e:
        # Änderung: exception() für Stacktrace im Log
        tg_logger.exception("Fehler beim API Call Filme/Serien/Episoden")
        items = []

    # Aufteilen nach Typ
    data = {
        "series": [],
        "movies": [],
        "episodes": [],
        "livetv": []
    }

    for item in items:
        type_ = item.get("Type")
        if type_ == "Series":
            data["series"].append(item)
        elif type_ == "Movie":
            data["movies"].append(item)
        elif type_ == "Episode":
            data["episodes"].append(item)

    # Live-TV-Kanäle laden | muss extra API Call gemacht werden.
    try:
        livetv_url = f"{jellyfin_url}/LiveTv/Channels"
        r2 = requests.get(livetv_url, headers=headers)
        r2.raise_for_status()
        channels = r2.json().get("Items", [])
        data["livetv"] = channels
    except Exception as e:
        # Änderung: exception() für Stacktrace im Log
        tg_logger.exception("Fehler beim API Call Live-TV")

    tg_logger.info("Hole & Erstelle Jellyfin Data - Done")
    return data
