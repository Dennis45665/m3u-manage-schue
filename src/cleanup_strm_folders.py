import shutil
from pathlib import Path
from logger import logger, log_start, log_end
from functions import load_config


def dir_has_strm(p: Path) -> bool:
    try:
        next(p.rglob('*.strm'))
        return True
    except StopIteration:
        return False


def cleanup_movies(path_movie: Path) -> int:
    logger.info("= Filme: Prüfe Ordner auf .strm …")
    removed = 0
    if not path_movie.exists():
        logger.info(f"Film-Pfad existiert nicht: {path_movie}")
        return 0
    for child in sorted(path_movie.iterdir()):
        if not child.is_dir():
            continue
        if not dir_has_strm(child):
            try:
                shutil.rmtree(child)
                removed += 1
                logger.info(f"Film-Ordner ohne .strm gelöscht: {child}")
            except OSError as e:
                logger.info(f"Fehler beim Löschen von {child}: {e}")
    logger.info(f"= Filme: Entfernte Ordner: {removed}")
    return removed


def cleanup_series(path_series: Path) -> tuple[int, int]:
    logger.info("= Serien: Prüfe Staffel-/Serien-Ordner auf .strm …")
    removed_seasons = 0
    removed_series = 0

    if not path_series.exists():
        logger.info(f"Serien-Pfad existiert nicht: {path_series}")
        return 0, 0

    for series_dir in sorted(path_series.iterdir()):
        if not series_dir.is_dir():
            continue

        # Staffeln ohne .strm entfernen
        for season_dir in sorted(series_dir.iterdir()):
            if not season_dir.is_dir():
                continue
            if not dir_has_strm(season_dir):
                try:
                    shutil.rmtree(season_dir)
                    removed_seasons += 1
                    logger.info(f"Staffel-Ordner ohne .strm gelöscht: {season_dir}")
                except OSError as e:
                    logger.info(f"Fehler beim Löschen von {season_dir}: {e}")

        # Serie löschen, wenn keine Staffel-Ordner mehr vorhanden ODER keine .strm mehr in der Serie
        try:
            season_dirs_left = [d for d in series_dir.iterdir() if d.is_dir()]
        except FileNotFoundError:
            # Wurde ggf. bereits entfernt, wenn parent leer war
            continue

        if not season_dirs_left or not dir_has_strm(series_dir):
            try:
                shutil.rmtree(series_dir)
                removed_series += 1
                logger.info(f"Serien-Ordner gelöscht: {series_dir}")
            except OSError as e:
                logger.info(f"Fehler beim Löschen von {series_dir}: {e}")

    logger.info(f"= Serien: Entfernte Staffeln: {removed_seasons}, entfernte Serien: {removed_series}")
    return removed_seasons, removed_series


def main():
    log_start()

    _, path_movie, path_serien, _, _ = load_config()
    movies_path = Path(path_movie)
    series_path = Path(path_serien)

    cleanup_movies(movies_path)
    cleanup_series(series_path)

    log_end()


if __name__ == "__main__":
    main()

