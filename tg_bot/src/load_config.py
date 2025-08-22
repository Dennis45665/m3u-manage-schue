import configparser
import re
from ..logger import tg_logger
from dotenv import load_dotenv
from pathlib import Path


def load_config():
    # Gehe ein Verzeichnis nach oben für die Konfigurationsdateien
    base_dir = Path(__file__).parent.parent.parent

    env_path = base_dir / ".env"
    config_path = base_dir / "CONFIG.ini"

    if env_path.exists():
        # .env Datei laden
        load_dotenv(env_path)
        jellyfin_url = os.getenv("jellyfin_url")
        jellyfin_api_key = os.getenv("jellyfin_api_key")
        tg_bot_token = os.getenv("tg_bot_token")
        tg_chat_id = os.getenv("tg_chat_id")
        hours_new_film_series = os.getenv("hours_new_film_series")

        tg_logger.info("TG-Config aus .env geladen")
    else:
        # config.ini laden
        config = configparser.ConfigParser()
        config.read(config_path)

        jellyfin_url = config['JELLYFIN_API']['jellyfin_url']
        jellyfin_api_key = config['JELLYFIN_API']['jellyfin_api_key']
        tg_bot_token = config['TG_BOT']['tg_bot_token']
        tg_chat_id = config['TG_BOT']['tg_chat_id']
        hours_new_film_series = config['JELLYFIN_API']['hours_new_film_series']

        tg_logger.info("Config aus CONFIG.ini geladen")

    tg_logger.info(f"Jellyfin URL: {jellyfin_url}")
    tg_logger.info(f"Jellyfin API KEY: {jellyfin_api_key}")
    tg_logger.info(f"Jellyfin Schedule New Film Series: {hours_new_film_series}")
    tg_logger.info(f"TG Bot Token: {tg_bot_token}")
    tg_logger.info(f"TG Chat ID: {tg_chat_id}")

    return jellyfin_url, jellyfin_api_key, tg_bot_token, tg_chat_id, hours_new_film_series