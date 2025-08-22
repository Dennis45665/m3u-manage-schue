from ..logger import tg_logger
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

    # Kombinierte Liste von alten und neuen Kanälen erstellen
    all_channels = old_channels + new_channels
    # Die kombinierte Liste speichern
    tmp_file.write_text(json.dumps(all_channels, indent=2, ensure_ascii=False), encoding="utf-8")

    return new_channels


def filter_movies(current_movies):
    base_dir = Path(__file__).resolve().parent.parent
    tmp_dir = base_dir / "tmp"
    tmp_file = tmp_dir / "movies.json"

    # Ordner /tmp erstellen, falls nicht vorhanden
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Alte Filme laden
    old_movies = []
    if tmp_file.exists():
        try:
            old_movies = json.loads(tmp_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old_movies = []

    # Vergleichen anhand des Filmnamens
    old_names = {m.get("Name") for m in old_movies}
    new_movies = [m for m in current_movies if m.get("Name") not in old_names]

    # Kombinierte Liste von alten und neuen Filmen erstellen
    all_movies = old_movies + new_movies
    # Die kombinierte Liste speichern
    tmp_file.write_text(json.dumps(all_movies, indent=2, ensure_ascii=False), encoding="utf-8")

    return new_movies


def filter_series(current_series):
    base_dir = Path(__file__).resolve().parent.parent
    tmp_dir = base_dir / "tmp"
    tmp_file = tmp_dir / "series.json"

    # Ordner /tmp erstellen, falls nicht vorhanden
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Alte Serien laden
    old_series = []
    if tmp_file.exists():
        try:
            old_series = json.loads(tmp_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old_series = []

    # Vergleichen anhand des Seriennamens
    old_names = {s.get("Name") for s in old_series}
    new_series = [s for s in current_series if s.get("Name") not in old_names]

    # Kombinierte Liste von alten und neuen Serien erstellen
    all_series = old_series + new_series
    # Die kombinierte Liste speichern
    tmp_file.write_text(json.dumps(all_series, indent=2, ensure_ascii=False), encoding="utf-8")

    return new_series


def filter_data(data):
    tg_logger.info("Filter Data ...")

    filtered = {
        "movies": filter_movies(data.get("movies", [])),
        "series": filter_series(data.get("series", [])),
        "episodes": group_episodes_by_series_and_season(data.get("episodes", [])),
        "livetv": filter_livetv_channels(data.get("livetv", []))
    }
    tg_logger.info("Filter Data - Done")
    return filtered