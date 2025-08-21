from pathlib import Path
from functions import sanitize_filename
from logger import logger

def save_new_movies_m3u(filename, path, blocklist):
    logger.info("=" * 30)
    logger.info("Check / Erstelle Filme")
    logger.info("=" * 30)

    tmp_dir = Path.cwd() / "tmp"
    input_file = tmp_dir / filename
    target_base_path = Path(path)

    # M3U-Datei lesen
    lines = input_file.read_text(encoding='utf-8', errors='ignore').splitlines()

    i = 1  # Start bei Zeile 1 (Zeile 0 ist #EXTM3U)
    while i < len(lines) - 1:
        line_info = lines[i].strip()
        line_url = lines[i + 1].strip()

        if line_info.startswith("#EXTINF:-1,"):
            title = line_info.replace("#EXTINF:-1,", "").strip()
        else:
            i += 2
            continue

        # Bereinigt den Titel für die Verwendung als Dateiname.
        safe_title = sanitize_filename(title)

        # Prüft, ob der bereinigte Titel in der Blockliste enthalten ist.
        if safe_title in blocklist:
            logger.info(f"Gesperrt: {title}")
            i += 2
            continue
        folder_path = target_base_path / safe_title
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / f"{safe_title}.strm"

        # Wenn Datei nicht existiert → erstellen
        if not file_path.exists():
            file_path.write_text(line_url, encoding='utf-8')
            logger.info(f"Erstellt: {file_path}")
        else:
            # Existierenden Link vergleichen
            existing_url = file_path.read_text(encoding='utf-8').strip()
            if existing_url != line_url:
                logger.info(f"Link geändert: {existing_url} → {line_url}")
                file_path.unlink()
                file_path.write_text(line_url, encoding='utf-8')
                logger.info(f"Aktualisiert: {file_path}")
            else:
                logger.info(f"Unverändert: {file_path}")

        i += 2  # nächstes Paar