from .logger import tg_logger, log_start, log_end
from .src.load_config import load_config
from .src.get_jellyfin_data import get_jellyfin_data
from .src.send_telegram_message import send_telegram_message
from .src.state import load_snapshot, save_snapshot, compute_new_items
from .src.filter_data import group_episodes_by_series_and_season

def main():
    """
    Hauptfunktion des Skripts.
    Lädt die Konfiguration, ruft Daten von Jellyfin ab, prüft auf neue Medien
    und sendet eine Benachrichtigung an Telegram, wenn neue Medien gefunden wurden.
    """
    log_start()
    tg_logger.info("Schritt 1/5: Lade Konfiguration…")
    jellyfin_url, jellyfin_api_key, tg_bot_token, tg_chat_id, hours_new_film_series = load_config()
    # Änderung: Zeitfenster wird nicht mehr genutzt – voller Abgleich.
    tg_logger.info("Hinweis: Zeitfenster wird ignoriert – vollständiger Vergleich zum letzten Lauf.")

    tg_logger.info("Schritt 2/5: Frage Jellyfin nach allen Inhalten…")
    current_data = get_jellyfin_data(jellyfin_url, jellyfin_api_key)

    if not current_data:
        tg_logger.info("Keine Daten von Jellyfin erhalten.")
        log_end()
        return

    tg_logger.info("Schritt 3/5: Lade vorherigen Snapshot…")
    prev_snapshot = load_snapshot()

    if prev_snapshot is None:
        tg_logger.info("Erster Start erkannt: Erstelle Snapshot und sende keine Nachrichten.")
        save_snapshot(current_data)
        tg_logger.info("Initialer Snapshot gespeichert.")
        log_end()
        return

    tg_logger.info("Schritt 4/5: Vergleiche Snapshots und ermittle neue Inhalte…")
    new_data = compute_new_items(prev_snapshot, current_data)

    # Änderung: Serien-Unterdrückung
    # Serien nicht als "neu" melden, wenn sie bereits in einem
    # vorherigen Snapshot existierten (auch wenn nur neue Staffeln/Folgen kamen).
    prev_series_ids = {s.get("Id") for s in (prev_snapshot.get("series", []) or []) if s.get("Id")}
    # Zusätzlich: Serien, die durch vorhandene Episoden im vorherigen Snapshot existierten
    prev_episode_series_ids = {e.get("SeriesId") for e in (prev_snapshot.get("episodes", []) or []) if e.get("SeriesId")}
    existing_series_ids = prev_series_ids.union(prev_episode_series_ids)

    if new_data.get("series"):
        filtered_series = [s for s in new_data["series"] if s.get("Id") not in existing_series_ids]
        dropped = len(new_data["series"]) - len(filtered_series)
        if dropped > 0:
            tg_logger.info(f"Unterdrücke {dropped} Serien, da bereits vorhanden (neue Staffeln/Folgen werden separat gemeldet).")
        new_data["series"] = filtered_series

    # Änderung: Episoden gruppieren für schönere Ausgabe (Sxx, Eyy–Ezz)
    if new_data.get("episodes"):
        new_data["episodes"] = group_episodes_by_series_and_season(new_data["episodes"])

    if any(new_data.get(k) for k in ("movies", "series", "episodes")):
        tg_logger.info("Neue Inhalte gefunden – bereite Versand vor…")
        dry_run = not (tg_bot_token and tg_chat_id)
        if dry_run:
            tg_logger.info("Telegram-Daten fehlen – führe DRY-RUN aus (zeige Nachrichten-Vorschau).")
        # Änderung: Nachrichten senden oder als Vorschau (Dry-Run) ausgeben
        send_telegram_message(
            tg_bot_token,
            tg_chat_id,
            new_data,
            current_data,
            dry_run=dry_run,
            save_sent_ids=False,
        )
    else:
        tg_logger.info("Keine neuen Inhalte seit dem letzten Lauf gefunden.")

    tg_logger.info("Schritt 5/5: Aktualisiere Snapshot…")
    save_snapshot(current_data)
    tg_logger.info("Snapshot aktualisiert. Ende.")

    log_end()



if __name__ == '__main__':
    main()
