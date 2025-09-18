from pathlib import Path
import shutil
from functions import sanitize_filename
from logger import logger
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.url_check import is_url_downloadable_with_reason
from src.offline_tracker import add_offline

def save_new_movies_m3u(filename, path, blocklist):
    logger.info("=" * 30)
    logger.info("Check / Erstelle Filme")
    logger.info("=" * 30)

    tmp_dir = Path.cwd() / "tmp"
    input_file = tmp_dir / filename
    target_base_path = Path(path)

    # 1. Erfasse alle vorhandenen .strm-Dateien
    existing_strm_files = set(target_base_path.rglob("*.strm"))
    processed_strm_files = set()
    created_titles = []
    deleted_titles = []

    # M3U-Datei lesen
    lines = input_file.read_text(encoding='utf-8', errors='ignore').splitlines()

    # 1) Einträge parsen (Titel/URL), Blockliste sofort anwenden
    entries = []  # {title, safe_title, url}
    i = 1  # Start bei Zeile 1 (Zeile 0 ist #EXTM3U)
    while i < len(lines) - 1:
        line_info = lines[i].strip()
        line_url = lines[i + 1].strip()

        if not line_info.startswith("#EXTINF:-1,"):
            i += 2
            continue

        title = line_info.replace("#EXTINF:-1,", "").strip()
        safe_title = sanitize_filename(title)

        if safe_title in blocklist:
            logger.info(f"Gesperrt: {title}")
            i += 2
            continue

        entries.append({"title": title, "safe_title": safe_title, "url": line_url})
        i += 2

    # 2) URL-Checks parallel (dedupliziert)
    url_to_titles = {}
    for e in entries:
        url_to_titles.setdefault(e["url"], []).append(e["title"])
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

    # 3) Dateien anlegen/aktualisieren basierend auf Check-Ergebnis
    for e in entries:
        title = e["title"]
        safe_title = e["safe_title"]
        line_url = e["url"]

        ok, reason = results.get(line_url, (False, "unknown"))
        if not ok:
            logger.info(f"Übersprungen (nicht downloadbar): {title} ({reason})")
            add_offline(title, line_url, kind="movie", reason=reason)
            continue

        folder_path = target_base_path / safe_title
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / f"{safe_title}.strm"
        processed_strm_files.add(file_path)

        if not file_path.exists():
            file_path.write_text(line_url, encoding='utf-8')
            logger.info(f"Erstellt: {file_path}")
            created_titles.append(title)
        else:
            existing_url = file_path.read_text(encoding='utf-8').strip()
            if existing_url != line_url:
                logger.info(f"Link geändert: {existing_url} → {line_url}")
                file_path.unlink()
                file_path.write_text(line_url, encoding='utf-8')
                logger.info(f"Aktualisiert: {file_path}")
            else:
                logger.info(f"Unverändert: {file_path}")

    # 3. Vergleiche und lösche veraltete Dateien
    strm_files_to_delete = existing_strm_files - processed_strm_files
    for file_path in strm_files_to_delete:
        try:
            parent_dir = file_path.parent
            # Datei löschen
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Gelöscht: {file_path}")
            deleted_titles.append(file_path.stem)

            # Kompletten Film-Ordner entfernen (inkl. evtl. verbleibender Dateien)
            if parent_dir.exists():
                shutil.rmtree(parent_dir)
                logger.info(f"Film-Ordner gelöscht: {parent_dir}")

        except OSError as e:
            logger.error(f"Fehler beim Löschen von {file_path} oder dem Verzeichnis: {e}")

    return created_titles, deleted_titles
