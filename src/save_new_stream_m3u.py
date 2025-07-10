import os
import shutil
from pathlib import Path
from logger import logger

def save_new_stream_m3u(filename, path_m3u):
    logger.info("=" * 30)
    logger.info("Check / Erstelle Stream m3u File")
    logger.info("=" * 30)

    # Pfade vorbereiten
    tmp_dir = Path.cwd() / "tmp"
    input_file = tmp_dir / filename
    path_m3u = Path(path_m3u)

    # 1. Suche nach existierender Datei mit "streams_" Prefix
    existing_file = next((f for f in path_m3u.glob("streams_*.m3u")), None)

    # 2. Keine bestehende Datei gefunden → direkt speichern
    if existing_file is None:
        new_path = path_m3u / filename
        shutil.copy2(input_file, new_path)
        logger.info(f"Neue Stream-Datei gespeichert: {new_path}")
        return

    # 3. Bestehende Datei gefunden → Zeilenweise vergleichen
    new_lines = input_file.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True)
    old_lines = existing_file.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True)

    # 4. Unterschied festgestellt → alte Datei löschen, neue unter neuem Namen speichern
    if new_lines != old_lines:
        logger.info("Änderung erkannt – ersetze alte Datei.")
        existing_file.unlink()
        new_path = path_m3u / filename
        shutil.copy2(input_file, new_path)
        logger.info(f"Neue Datei gespeichert: {new_path}")
    else:
        logger.info("Keine Änderung – bestehende Datei bleibt erhalten.")