from app.core.config import load_config
from app.core.logger import setup_logging
from app.core.database import create_database
from app.adb.adb_manager import ADBManager


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

        else:
            self.logger.error(
                "ADB unavailable"
            )

        self.logger.info(
            "PixelSync ready"
        )