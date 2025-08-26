import logging
from pathlib import Path
from datetime import datetime
import sys

log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

def cleanup_logs(max_files=10):
    logs = sorted(log_dir.glob("*_m3u_log.log"), key=lambda f: f.stat().st_mtime)
    if len(logs) > max_files:
        to_delete = logs[:-max_files]
        for file in to_delete:
            # Verwende logger, um auch das Löschen alter Logs zu protokollieren
            logger.info(f"Lösche alte Logdatei: {file.name}")
            file.unlink()

def get_log_file():
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return log_dir / f"{now_str}_m3u_log.log"

# Logger konfigurieren
logger = logging.getLogger("m3u_logger")
logger.setLevel(logging.INFO)

# Verhindern, dass Handler mehrfach hinzugefügt werden, falls das Modul neu geladen wird
if not logger.handlers:
    log_file = get_log_file()
    
    # Formatter erstellen
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # File Handler erstellen
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Stream Handler (für Konsolenausgabe) erstellen
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # Handler zum Logger hinzufügen
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Alte Logs aufräumen, nachdem der Logger konfiguriert ist
    cleanup_logs()


def log_start():
    logger.info("=" * 60)
    logger.info("STARTE M3U-SKRIPT")
    logger.info("=" * 60)

def log_end():
    logger.info("=" * 60)
    logger.info("M3U-SKRIPT BEENDET")
    logger.info("=" * 60)