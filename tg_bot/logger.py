import logging
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

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

tg_logger = logging.getLogger("tg_logger")


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
