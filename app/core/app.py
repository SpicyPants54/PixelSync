from pathlib import Path

from app.core.config import load_config
from app.core.logger import setup_logging
from app.core.database import create_database
from app.adb.adb_manager import ADBManager
from app.adb.transfer import TransferManager


class PixelSyncApp:

    def __init__(self):

        self.config = load_config()

        self.logger = setup_logging(
            self.config.log_folder
        )

        self.database = create_database(
            self.config.database_file
        )

        self.adb = ADBManager()

        self.transfer = None


    def start(self):

        self.logger.info(
            "PixelSync starting..."
        )

        if self.adb.check_adb():

            if self.adb.connect():

                model = self.adb.get_model()

                self.logger.info(
                    f"Device model: {model}"
                )

                self.transfer = TransferManager(
                    self.adb.device
                )

                self.logger.info(
                    "Transfer engine ready"
                )

                test_file = (
                    Path.home()
                    / "Pictures"
                    / "PixelSync Import"
                    / "test.jpg"
                )

                if test_file.exists():

                    self.transfer.push_file(
                        test_file,
                        "/sdcard/DCIM/Camera/"
                    )

                else:

                    self.logger.warning(
                        f"Test file not found: {test_file}"
                    )

        else:

            self.logger.error(
                "ADB unavailable"
            )


        self.logger.info(
            "PixelSync ready"
        )