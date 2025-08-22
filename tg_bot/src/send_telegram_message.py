import time
import json
from tg_bot.logger import tg_logger
import requests
from pathlib import Path

# Pfad zur Datei, in der die gesendeten IDs gespeichert werden
SENT_ITEMS_FILE = Path(__file__).parent.parent / "tmp" / "sent_items.json"

def send_message(tg_bot_token, tg_chat_id, text):
    tg_logger.info("Sende TG Message...")

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{tg_bot_token}/sendMessage",
            data={
                "chat_id": tg_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
        )
        if response.status_code != 200:
            tg_logger.error(f"Telegram API Fehler {response.status_code}: {response.text}")
        else:
            json_response = response.json()
            if not json_response.get("ok"):
                tg_logger.error(f"Telegram-Fehlermeldung: {json_response}")
            else:
                tg_logger.info("Nachricht erfolgreich gesendet.")
                return True

    except requests.exceptions.RequestException as e:
        tg_logger.exception(f"Fehler beim Senden der Nachricht: {e}")
    return False


def format_telegram_message(data, max_length=4000):
    def build_section_text(title, items, formatter):
        bold_title = f"**{title.lstrip('# ').strip()}**"
        lines = [bold_title]
        for item in items:
            lines.append(formatter(item))
        return "\n".join(lines)

    sections = []

    if data.get("movies"):
        sections.append(build_section_text("🎬 Filme", data["movies"], lambda m: f"- {m['Name']}"))

    if data.get("series"):
        sections.append(build_section_text("📺 Serien", data["series"], lambda s: f"- {s['Name']}"))

    if data.get("episodes"):
        def ep_formatter(e):
            return f"- {e['SeriesName']} – {e['SeasonName']} ({e['EpisodeRange']})"
        sections.append(build_section_text("📼 Neue Episoden", data["episodes"], ep_formatter))

    if data.get("livetv"):
        sections.append(build_section_text("📡 Neue Live-TV-Kanäle", data["livetv"], lambda c: f"- {c['Name']}"))

    full_text = "**🚀 Neue Medien in SurkFlix 🚀**\n\n" + "\n\n".join(sections)

    if len(full_text) <= max_length:
        return [full_text]

    messages = []
    current_msg = "**🚀 Neue Medien in SurkFlix 🚀**"
    current_len = len(current_msg) + 2

    part_num = 1

    for section in sections:
        section_len = len(section) + 2

        if section_len > max_length:
            lines = section.split("\n")
            buffer = []
            buffer_len = 0

            for line in lines:
                line_len = len(line) + 1
                if buffer_len + line_len > max_length:
                    header = f"**🚀 Neue Medien in SurkFlix 🚀** {part_num}/??"
                    messages.append(header + "\n\n" + "\n".join(buffer))
                    part_num += 1
                    buffer = [line]
                    buffer_len = len(line) + 1
                else:
                    buffer.append(line)
                    buffer_len += line_len

            if buffer:
                header = f"**🚀 Neue Medien in SurkFlix 🚀** {part_num}/??"
                messages.append(header + "\n\n" + "\n".join(buffer))
                part_num += 1

        else:
            if current_len + section_len <= max_length:
                current_msg += "\n\n" + section
                current_len += section_len
            else:
                header = f"**🚀 Neue Medien in SurkFlix 🚀** {part_num}/??"
                messages.append(header + "\n\n" + current_msg[len("**🚀 Neue Medien in SurkFlix 🚀**"):].strip())
                part_num += 1

                current_msg = section
                current_len = section_len

    if current_msg.strip():
        header = f"**🚀 Neue Medien in SurkFlix 🚀** {part_num}/??"
        messages.append(header + "\n\n" + current_msg[len("**🚀 Neue Medien in SurkFlix 🚀**"):].strip())

    total_parts = len(messages)
    for i in range(total_parts):
        messages[i] = messages[i].replace("??", str(total_parts))
        if total_parts == 1:
            messages[i] = messages[i].replace(f" {i+1}/{total_parts}", "")

    return messages


def send_telegram_message(tg_bot_token, tg_chat_id, data, unfiltered_data):
    """
    Formatiert die Daten und sendet sie als eine oder mehrere Telegram-Nachrichten.
    Speichert die IDs der gesendeten Medien, um Duplikate zu vermeiden.

    Args:
        tg_bot_token (str): Der Token für den Telegram-Bot.
        tg_chat_id (str): Die ID des Telegram-Chats, an den die Nachrichten gesendet werden sollen.
        data (dict): Die zu sendenden Daten, gefiltert nach neuen Medien.
        unfiltered_data (dict): Die ursprünglichen, ungefilterten Daten von Jellyfin.
    """
    tg_logger.info("Start - Sende TG Message mit Jellyfin Data")

    # Telegram message formatieren
    messages = format_telegram_message(data)
    
    all_sent_successfully = True
    # Einzelne Nachrichten nacheinander senden
    for msg in messages:
        if not send_message(tg_bot_token, tg_chat_id, msg):
            all_sent_successfully = False
            break  # Stop sending if one message fails
        time.sleep(5)

    if all_sent_successfully:
        save_last_run_data(unfiltered_data)
        tg_logger.info("Alle Nachrichten erfolgreich gesendet und Daten gespeichert.")
    else:
        tg_logger.error("Nicht alle Nachrichten konnten gesendet werden. Daten werden nicht gespeichert.")

    tg_logger.info("Sende TG Message mit Jellyfin Data - Done")


def save_last_run_data(data):
    """
    Speichert die IDs der gesendeten Medien in einer JSON-Datei, um zukünftige Duplikate zu verhindern.

    Args:
        data (dict): Die Daten der Medien, deren IDs gespeichert werden sollen.
    """
    try:
        # Lade vorhandene Daten
        if SENT_ITEMS_FILE.exists():
            with open(SENT_ITEMS_FILE, "r", encoding="utf-8") as f:
                sent_data = json.load(f)
        else:
            sent_data = {"movies": [], "series": [], "episodes": []}

        # Füge neue IDs hinzu
        for key in ["movies", "series", "episodes"]:
            if key in data:
                for item in data[key]:
                    if item["Id"] not in sent_data[key]:
                        sent_data[key].append(item["Id"])
        
        # Speichere die aktualisierten Daten
        SENT_ITEMS_FILE.parent.mkdir(exist_ok=True)
        with open(SENT_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(sent_data, f, indent=4)
            
        tg_logger.info(f"Gesendete Daten in {SENT_ITEMS_FILE} gespeichert.")

    except Exception as e:
        tg_logger.exception(f"Fehler beim Speichern der Daten: {e}")


def has_new_data(current_data):
    """
    Vergleicht die aktuellen Daten von Jellyfin mit den bereits gesendeten IDs.

    Args:
        current_data (dict): Die aktuellen Daten von Jellyfin.

    Returns:
        dict: Ein Dictionary, das nur die neuen, noch nicht gesendeten Medien enthält.
    """
    if not SENT_ITEMS_FILE.exists():
        return current_data # Wenn keine Datei existiert, sind alle Daten neu

    try:
        with open(SENT_ITEMS_FILE, "r", encoding="utf-8") as f:
            sent_ids = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        sent_ids = {"movies": [], "series": [], "episodes": []}

    new_data = {}
    for key in ["movies", "series", "episodes"]:
        if key in current_data:
            new_items = [item for item in current_data[key] if item["Id"] not in sent_ids.get(key, [])]
            if new_items:
                new_data[key] = new_items

    return new_data
