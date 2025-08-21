import os
import configparser
import re
from logger import logger
from dotenv import load_dotenv
from pathlib import Path

def load_config():
    dotenv_path = Path(".env")
    if dotenv_path.exists():
        # .env Datei laden
        load_dotenv(dotenv_path)
        url = os.getenv("url")
        main_path = os.getenv("main_path")
        path_movie = os.path.join(main_path, os.getenv("path_movie"))
        path_serien = os.path.join(main_path, os.getenv("path_serien"))
        path_m3u = os.path.join(main_path, os.getenv("path_m3u"))
        blockliste_path = os.path.join(main_path, os.getenv("blockliste_path"))

        logger.info("Config aus .env geladen")
    else:
        # config.ini laden
        config = configparser.ConfigParser()
        config.read('CONFIG.ini')

        url = config['M3U']['url']
        main_path = config['PATH']['main_path']
        path_movie = os.path.join(main_path, config['PATH']['path_movie'])
        path_serien = os.path.join(main_path, config['PATH']['path_serien'])
        path_m3u = os.path.join(main_path, config['PATH']['path_m3u'])
        blockliste_path = os.path.join(main_path, config['PATH']['path_blockliste'])


        logger.info("Config aus CONFIG.ini geladen")

    logger.info(f"M3U Url: {url}")
    logger.info(f"Main Path: {main_path}")
    logger.info(f"Path zu Filme: {path_movie}")
    logger.info(f"Path zu Serien: {path_serien}")
    logger.info(f"Path zur M3U Datei / Streams: {path_m3u}")
    logger.info(f"Path zur Blockliste: {blockliste_path}")

    return url, path_movie, path_serien, path_m3u, blockliste_path


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def load_blocklist(blocklist_path: str) -> set:
    """
    Lädt die Blocklistendatei und gibt ein Set mit den blockierten Titeln zurück.

    :param blocklist_path: Der Pfad zur Blocklistendatei.
    :return: Ein Set mit den blockierten Titeln.
    """
    # Prüft, ob die Blocklistendatei existiert.
    if not os.path.exists(blocklist_path):
        logger.warning(f"Blocklistendatei nicht gefunden unter: {blocklist_path}")
        return set()
    # Öffnet die Blocklistendatei und liest die Zeilen in ein Set ein.
    with open(blocklist_path, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f}
