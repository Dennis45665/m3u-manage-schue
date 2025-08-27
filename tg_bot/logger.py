import logging
import sys  # Änderung: Konsolen-Logging über stdout hinzufügen
from pathlib import Path
from datetime import datetime

log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

def cleanup_logs(max_files=10):
    logs = sorted(log_dir.glob("*_tg_bot_log.log"), key=lambda f: f.stat().st_mtime)
    if len(logs) > max_files:
        to_delete = logs[:-max_files]
        for file in to_delete:
            print(f"Lösche alte Logdatei: {file.name}")
            file.unlink()

def get_log_file():
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return log_dir / f"{now_str}_tg_bot_log.log"

log_file = get_log_file()
cleanup_logs()

tg_logger = logging.getLogger("tg_logger")
tg_logger.setLevel(logging.INFO)

# Änderung: Eigenes Logging-Setup mit File- und Console-Handler,
# statt nur basicConfig mit Datei.
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
tg_logger.addHandler(file_handler)

# Console Handler (direkte Ausgabe in Terminal)
console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
tg_logger.addHandler(console_handler)

tg_logger.propagate = False


def log_start():
    print("STARTE TG_JELLYFIN_API-SKRIPT")
    tg_logger.info("=" * 60)
    tg_logger.info("STARTE M3U-SKRIPT")
    tg_logger.info("=" * 60)

def log_end():
    print("TG_JELLYFIN_API-SKRIPT BEENDET")
    tg_logger.info("=" * 60)
    tg_logger.info("M3U-SKRIPT BEENDET")
    tg_logger.info("=" * 60)
