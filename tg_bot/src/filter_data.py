from tg_bot.logger import tg_logger
from collections import defaultdict
import json
from pathlib import Path

def group_episodes_by_series_and_season(episodes):
    grouped = defaultdict(list)

    for ep in episodes:
        key = (ep.get("SeriesName"), ep.get("SeasonName"))
        grouped[key].append(ep)

    result = []

    for (series_name, season_name), eps in grouped.items():
        eps_sorted = sorted(eps, key=lambda x: x.get("IndexNumber") or 0)
        episode_numbers = [e.get("IndexNumber") for e in eps_sorted if e.get("IndexNumber") is not None]

        if not episode_numbers:
            continue

        if len(episode_numbers) == 1:
            episode_str = f"E{episode_numbers[0]:02}"
        else:
            episode_str = f"E{episode_numbers[0]:02}–E{episode_numbers[-1]:02}"

        result.append({
            "SeriesName": series_name,
            "SeasonName": season_name,
            "EpisodeRange": episode_str
        })

    return result


def filter_livetv_channels(current_channels):
    base_dir = Path(__file__).resolve().parent.parent
    tmp_dir = base_dir / "tmp"
    tmp_file = tmp_dir / "livetv_channels.json"

    # Ordner /tmp erstellen, falls nicht vorhanden
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Alte Kanäle laden
    old_channels = []
    if tmp_file.exists():
        try:
            old_channels = json.loads(tmp_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old_channels = []

    # Vergleichen anhand des Kanalnamens
    old_names = {c.get("Name") for c in old_channels}
    new_channels = [c for c in current_channels if c.get("Name") not in old_names]

    # Neue Daten speichern
    tmp_file.write_text(json.dumps(current_channels, indent=2, ensure_ascii=False), encoding="utf-8")

    return new_channels

def filter_data(data):
    tg_logger.info("Filter Data ...")

    filtered = {
        "movies": data.get("movies", []),
        "series": data.get("series", []),
        "episodes": group_episodes_by_series_and_season(data.get("episodes", [])),
        "livetv": filter_livetv_channels(data.get("livetv", []))
    }
    tg_logger.info("Filter Data - Done")
    return filtered