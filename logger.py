import logging
from pathlib import Path
from datetime import datetime

log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

def cleanup_logs(max_files=10):
    logs = sorted(log_dir.glob("*_m3u_log.log"), key=lambda f: f.stat().st_mtime)
    if len(logs) > max_files:
        to_delete = logs[:-max_files]
        for file in to_delete:
            print(f"Lösche alte Logdatei: {file.name}")
            file.unlink()

def get_log_file():
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return log_dir / f"{now_str}_m3u_log.log"

log_file = get_log_file()
cleanup_logs()

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

logger = logging.getLogger("m3u_logger")


def log_start():
    print("STARTE M3U-SKRIPT")
    logger.info("=" * 60)
    logger.info("STARTE M3U-SKRIPT")
    logger.info("=" * 60)

def log_end():
    print("M3U-SKRIPT BEENDET")
    logger.info("=" * 60)
    logger.info("M3U-SKRIPT BEENDET")
    logger.info("=" * 60)
