import time

from tg_bot.logger import tg_logger
import requests
from pathlib import Path

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
        print(response.json())
        if response.status_code != 200:
            tg_logger.error(f"Telegram API Fehler {response.status_code}: {response.text}")
        else:
            json_response = response.json()
            if not json_response.get("ok"):
                tg_logger.error(f"Telegram-Fehlermeldung: {json_response}")
            else:
                tg_logger.info("Nachricht erfolgreich gesendet.")

    except requests.exceptions.RequestException as e:
        tg_logger.exception(f"Fehler beim Senden der Nachricht: {e}")



def format_telegram_message_old(data):
    lines = ["# 🚀 Neue Medien in SurkFlix 🚀"]

    if data.get("movies"):
        lines.append("\n## 🎬 Filme")
        for m in data["movies"]:
            lines.append(f"- {m['Name']}")

    if data.get("series"):
        lines.append("\n## 📺 Serien")
        for s in data["series"]:
            lines.append(f"- {s['Name']}")

    if data.get("episodes"):
        lines.append("\n## 📼 Neue Episoden")
        for e in data["episodes"]:
            series = e["SeriesName"]
            season = e["SeasonName"]
            ep_range = e["EpisodeRange"]
            lines.append(f"- {series} – {season} ({ep_range})")

    if data.get("livetv"):  # Jetzt wieder aktiv!
        lines.append("\n## 📡 Neue Live-TV-Kanäle")
        for c in data["livetv"]:
            lines.append(f"- {c['Name']}")

    #return "\n".join(lines)
    # In Datei speichern
    filepath = "test.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


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


def send_telegram_message(tg_bot_token, tg_chat_id, data):
    tg_logger.info("Start - Sende TG Message mit Jellyfin Data")

    # Telegram message formatieren
    messages = format_telegram_message(data)

    # Einzelne Nachrichten nacheinander senden
    for msg in messages:
        send_message(tg_bot_token, tg_chat_id, msg)
        time.sleep(5)

    tg_logger.info("Sende TG Message mit Jellyfin Data - Done")

