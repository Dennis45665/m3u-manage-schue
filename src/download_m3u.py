import logging
import os
import requests
from datetime import  datetime
from logger import logger
from pathlib import Path

def delete_all_files_in_tmp(tmp_dir):
    for filename in os.listdir(tmp_dir):
        file_path = os.path.join(tmp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                logger.info(f"Gelöscht: {file_path}")
        except Exception as e:
            logger.info(f"Fehler beim Löschen von {file_path}: {e}")




def download_m3u(url):
    logger.info(f"Download M3U von URL: {url}")

    # /tmp vorhanden?
    tmp_dir = Path.cwd() / "tmp"
    os.makedirs(tmp_dir, exist_ok=True)

    # Datein inhalten? -> löschen
    delete_all_files_in_tmp(tmp_dir)

    # Datei Downloaden
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        session = requests.Session()
        response = session.get(url, headers=headers)
        response.raise_for_status()  # Prüft auf HTTP-Fehler

        # Versuche, den Filename aus den Headern zu extrahieren
        content_disposition = response.headers.get("Content-Disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[1].strip('"')
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"playlist_{timestamp}.m3u"

        save_path = os.path.join(tmp_dir, filename)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Erfolgreich gespeichert unter: {save_path}")
        return filename

    except requests.exceptions.RequestException as e:
        logger.info(f"Download fehlgeschlagen: {e}")
        raise