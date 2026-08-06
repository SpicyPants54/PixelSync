from pathlib import Path
from pydantic import BaseModel


class PixelSyncConfig(BaseModel):
    import_folder: str = str(
        Path.home() / "Pictures" / "PixelSync Import"
    )

    pixel_folder: str = "/sdcard/DCIM/Camera"

    database_file: str = "pixelsync.db"

    log_folder: str = "logs"


def load_config():
    return PixelSyncConfig()