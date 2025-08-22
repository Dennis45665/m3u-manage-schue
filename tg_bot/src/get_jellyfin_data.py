import requests
from datetime import datetime, timedelta, timezone
from ..logger import tg_logger
import json

def get_jellyfin_data(jellyfin_url, jellyfin_api_key, hours=1):
    tg_logger.info("Hole & Erstelle Jellyfin Data")
    hours = float(hours)
    now = datetime.now(timezone.utc)
    min_date = now - timedelta(hours=hours)
    min_date_str = min_date.isoformat()

    headers = {
        "X-Emby-Token": jellyfin_api_key
    }

    base_items_url = f"{jellyfin_url}/emby/Items"
    item_params = {
        "IncludeItemTypes": "Series,Movie,Episode",
        "Recursive": "true",
        "Fields": "DateCreated,Path",
        "SortBy": "DateCreated",
        "SortOrder": "Descending",
        "MinDateCreated": min_date_str
    }

    try:
        r = requests.get(base_items_url, headers=headers, params=item_params)
        r.raise_for_status()
        items = r.json().get("Items", [])
        tg_logger.info(f"Jellyfin API response: {json.dumps(items, indent=2)}")
    except Exception as e:
        tg_logger.info("Fehler beim API Call Filme/Serien/Episoden", e)
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
        tg_logger.info("Fehler beim API Call Live-TV", e)

    tg_logger.info("Hole & Erstelle Jellyfin Data - Done")
    return data