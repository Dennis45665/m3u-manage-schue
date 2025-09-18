import re
from pathlib import Path
import shutil
from functions import sanitize_filename
from logger import logger
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.url_check import is_url_downloadable_with_reason
from src.offline_tracker import add_offline

def save_new_series_m3u(filename, path, blocklist):
    logger.info("=" * 30)
    logger.info("Check / Erstelle Serien")
    logger.info("=" * 30)

    tmp_dir = Path.cwd() / "tmp"
    input_file = tmp_dir / filename
    target_base_path = Path(path)

    # 1. Erfasse alle vorhandenen .strm-Dateien
    existing_strm_files = set(target_base_path.rglob("*.strm"))
    processed_strm_files = set()
    created_titles = []
    deleted_titles = []

    # M3U-Datei zeilenweise lesen
    lines = input_file.read_text(encoding='utf-8', errors='ignore').splitlines()

    # 1) Einträge parsen (Serienstruktur + Blockliste anwenden)
    entries = []  # {full_name, safe_full_name, series_name, safe_series_name, serien_ordner, staffel_ordner, url}
    i = 1
    while i < len(lines) - 1:
        extinf_line = lines[i].strip()
        url_line = lines[i+1].strip()

        if not extinf_line.startswith("#EXTINF:-1,"):
            i += 2
            continue

        full_name = extinf_line[len("#EXTINF:-1,"):]

        staffel_match = re.search(r'\sS(\d+)\sE(\d+)', full_name, re.IGNORECASE)
        if staffel_match:
            serien_name = full_name[:staffel_match.start()].strip()
            staffel_nummer = staffel_match.group(1)
        else:
            serien_name = full_name.strip()
            staffel_nummer = None

        safe_full_name = sanitize_filename(full_name)
        safe_serien_name = sanitize_filename(serien_name)

        if safe_full_name in blocklist or safe_serien_name in blocklist:
            logger.info(f"Gesperrt: {full_name}")
            i += 2
            continue

        serien_ordner = safe_serien_name
        if staffel_nummer is not None:
            staffel_ordner = f"Staffel {int(staffel_nummer):02d}"
        else:
            staffel_ordner = "Staffel Unbekannt"

        entries.append({
            "full_name": full_name,
            "safe_full_name": safe_full_name,
            "series_name": serien_name,
            "safe_series_name": safe_serien_name,
            "serien_ordner": serien_ordner,
            "staffel_ordner": staffel_ordner,
            "url": url_line,
        })
        i += 2

    # 2) URL-Checks parallel (dedupliziert)
    url_to_titles = {}
    for e in entries:
        url_to_titles.setdefault(e["url"], []).append(e["full_name"])
    unique_urls = list(url_to_titles.keys())

    def check(u: str):
        ok, reason = is_url_downloadable_with_reason(u)
        return u, ok, reason

    results = {}
    if unique_urls:
        with ThreadPoolExecutor(max_workers=30) as ex:
            future_to_url = {ex.submit(check, url): url for url in unique_urls}
            for fut in as_completed(future_to_url):
                url, ok, reason = fut.result()
                results[url] = (ok, reason)
                sample_title = url_to_titles.get(url, [url])[0]
                if ok:
                    logger.info(f"Geprüft: {sample_title} → OK")
                else:
                    logger.info(f"Geprüft: {sample_title} → FAIL ({reason})")

    # 3) Dateien anlegen/aktualisieren
    for e in entries:
        full_name = e["full_name"]
        safe_full_name = e["safe_full_name"]
        series_name = e["series_name"]
        serien_ordner = e["serien_ordner"]
        staffel_ordner = e["staffel_ordner"]
        url_line = e["url"]

        ok, reason = results.get(url_line, (False, "unknown"))
        if not ok:
            logger.info(f"Übersprungen (nicht downloadbar): {full_name} ({reason})")
            add_offline(series_name, url_line, kind="series", reason=reason)
            continue

        ziel_ordner = target_base_path / serien_ordner / staffel_ordner
        ziel_ordner.mkdir(parents=True, exist_ok=True)

        dateiname_strm = safe_full_name + ".strm"
        strm_datei = ziel_ordner / dateiname_strm
        processed_strm_files.add(strm_datei)

        if strm_datei.exists():
            bestehender_link = strm_datei.read_text(encoding='utf-8', errors='ignore').strip()
            if bestehender_link == url_line:
                logger.info(f"{strm_datei} existiert bereits mit gleichem Link.")
            else:
                logger.info(f"{strm_datei} existiert, Link anders – Datei wird aktualisiert.")
                strm_datei.unlink()
                strm_datei.write_text(url_line + "\n", encoding='utf-8')
        else:
            logger.info(f"➕ Erstelle neue Datei: {strm_datei}")
            strm_datei.write_text(url_line + "\n", encoding='utf-8')
            created_titles.append(full_name)

    # 3. Vergleiche und lösche veraltete Dateien
    strm_files_to_delete = existing_strm_files - processed_strm_files

    # Vorab: Season- und Serien-Gruppierung der vorhandenen Dateien (vor Löschung)
    from collections import defaultdict
    season_to_files = defaultdict(set)
    series_to_seasons = defaultdict(set)
    for f in existing_strm_files:
        season_dir = f.parent
        series_dir = season_dir.parent
        season_to_files[season_dir].add(f)
        series_to_seasons[series_dir].add(season_dir)

    # Gruppiere, welche Dateien pro Season gelöscht werden
    season_to_delete = defaultdict(set)
    for f in strm_files_to_delete:
        season_to_delete[f.parent].add(f)

    # 3a) Einzelne Dateien löschen
    for file_path in strm_files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Gelöscht: {file_path}")
            deleted_titles.append(file_path.stem)
        except OSError as e:
            logger.info(f"Fehler beim Löschen von {file_path}: {e}")

    # 3b) Ganze Staffeln löschen, wenn alle Episoden betroffen sind
    seasons_removed = set()
    for season_dir, del_set in season_to_delete.items():
        all_files_in_season = season_to_files.get(season_dir, set())
        if del_set and del_set == all_files_in_season:
            # komplette Staffel löschen (rekursiv), inkl. NFO/JPG etc.
            try:
                if season_dir.exists():
                    shutil.rmtree(season_dir)
                    logger.info(f"Staffel-Ordner gelöscht: {season_dir}")
                    seasons_removed.add(season_dir)
            except OSError as e:
                logger.info(f"Fehler beim Löschen des Staffel-Ordners {season_dir}: {e}")

    # 3c) Ganze Serien löschen, wenn alle Staffeln entfernt wurden
    for series_dir, seasons in series_to_seasons.items():
        if seasons and seasons.issubset(seasons_removed):
            try:
                if series_dir.exists():
                    shutil.rmtree(series_dir)
                    logger.info(f"Serien-Ordner gelöscht: {series_dir}")
            except OSError as e:
                logger.info(f"Fehler beim Löschen des Serien-Ordners {series_dir}: {e}")

    logger.info("Fertig mit Serien-Verarbeitung.")
    return created_titles, deleted_titles
