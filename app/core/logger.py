from pathlib import Path
from loguru import logger


def setup_logging(log_folder: str):

    Path(log_folder).mkdir(
        parents=True,
        exist_ok=True
    )

    logger.add(
        Path(log_folder) / "pixelsync.log",
        rotation="10 MB",
        retention="30 days"
    )

    logger.info("PixelSync logging started")

    return logger