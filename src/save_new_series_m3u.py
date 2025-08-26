import re
from pathlib import Path
from functions import sanitize_filename
from logger import logger
import os

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

    # M3U-Datei zeilenweise lesen
    lines = input_file.read_text(encoding='utf-8', errors='ignore').splitlines()

    i = 1
    while i < len(lines) - 1:
        extinf_line = lines[i].strip()
        url_line = lines[i+1].strip()

        if extinf_line.startswith("#EXTINF:-1,"):
            # Gesamter Name inklusive Staffel und Episode (für Dateiname)
            full_name = extinf_line[len("#EXTINF:-1,"):]

            # Serienname extrahieren OHNE Staffel/Episode für den Ordnernamen
            staffel_match = re.search(r'\sS(\d+)\sE(\d+)', full_name, re.IGNORECASE)
            if staffel_match:
                serien_name = full_name[:staffel_match.start()].strip()
                staffel_nummer = staffel_match.group(1)
            else:
                serien_name = full_name.strip()
                staffel_nummer = None

            # Bereinigt den vollständigen Namen und den Seriennamen für die Verwendung als Dateinamen.
            safe_full_name = sanitize_filename(full_name)
            safe_serien_name = sanitize_filename(serien_name)

            # Prüft, ob der bereinigte vollständige Name oder der bereinigte Serienname in der Blockliste enthalten ist.
            if safe_full_name in blocklist or safe_serien_name in blocklist:
                logger.info(f"Gesperrt: {full_name}")
                i += 2
                continue

            serien_ordner = safe_serien_name
            if staffel_nummer is not None:
                staffel_ordner = f"Staffel {int(staffel_nummer):02d}"
            else:
                staffel_ordner = "Staffel Unbekannt"

            # Ordnerpfad bauen und sicherstellen, dass er existiert
            ziel_ordner = target_base_path / serien_ordner / staffel_ordner
            ziel_ordner.mkdir(parents=True, exist_ok=True)

            # Dateiname aus dem kompletten EXTINF-Namen, als .strm
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

        i += 2

    # 3. Vergleiche und lösche veraltete Dateien
    strm_files_to_delete = existing_strm_files - processed_strm_files
    for file_path in strm_files_to_delete:
        try:
            season_dir = file_path.parent
            series_dir = season_dir.parent
            file_path.unlink()
            logger.info(f"Gelöscht: {file_path}")

            # 4. Prüfe und lösche leeres Staffel-Verzeichnis
            if not any(season_dir.iterdir()):
                season_dir.rmdir()
                logger.info(f"Leeres Staffel-Verzeichnis gelöscht: {season_dir}")

                # 5. Prüfe und lösche leeres Serien-Verzeichnis
                if not any(series_dir.iterdir()):
                    series_dir.rmdir()
                    logger.info(f"Leeres Serien-Verzeichnis gelöscht: {series_dir}")

        except OSError as e:
            logger.info(f"Fehler beim Löschen von {file_path} oder dem Verzeichnis: {e}")

    logger.info("Fertig mit Serien-Verarbeitung.")