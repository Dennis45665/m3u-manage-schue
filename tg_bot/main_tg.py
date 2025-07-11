import time

from logger import tg_logger, log_start, log_end
from src.load_config import load_config
from src.get_jellyfin_data import get_jellyfin_data
from src.send_telegram_message import send_telegram_message
from src.filter_data import filter_data

def main():
    log_start()
    # Config laden
    jellyfin_url, jellyfin_api_key, tg_bot_token, tg_chat_id, hours_new_film_series = load_config()

    # Jellyfin Daten holen
    data = get_jellyfin_data(jellyfin_url, jellyfin_api_key, hours_new_film_series)

    if data:
        filter_data_dic = filter_data(data)
        send_telegram_message(tg_bot_token, tg_chat_id, filter_data_dic)
    else: tg_logger.info("Keine neuen Daten gefunden - sende keine TG Message ...")

    log_end()



if __name__ == '__main__':
    main()