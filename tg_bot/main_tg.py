import time

from .logger import tg_logger, log_start, log_end
from .src.load_config import load_config
from .src.get_jellyfin_data import get_jellyfin_data
from .src.send_telegram_message import send_telegram_message, has_new_data
from .src.filter_data import filter_data

def main():
    """
    Hauptfunktion des Skripts.
    Lädt die Konfiguration, ruft Daten von Jellyfin ab, prüft auf neue Medien
    und sendet eine Benachrichtigung an Telegram, wenn neue Medien gefunden wurden.
    """
    log_start()
    # Config laden
    jellyfin_url, jellyfin_api_key, tg_bot_token, tg_chat_id, hours_new_film_series = load_config()

    # Jellyfin Daten holen
    unfiltered_data = get_jellyfin_data(jellyfin_url, jellyfin_api_key, hours_new_film_series)

    if unfiltered_data:
        # Prüfen, ob es neue, ungesendete Daten gibt
        new_data_to_send = has_new_data(unfiltered_data)
        
        if new_data_to_send:
            # Daten filtern und für die Nachricht vorbereiten
            filter_data_dic = filter_data(new_data_to_send)
            
            # Telegram-Nachricht senden
            send_telegram_message(tg_bot_token, tg_chat_id, filter_data_dic, unfiltered_data)
        else:
            tg_logger.info("Keine neuen Daten gefunden, die noch nicht gesendet wurden.")
    else: 
        tg_logger.info("Keine neuen Daten von Jellyfin erhalten.")

    log_end()



if __name__ == '__main__':
    main()