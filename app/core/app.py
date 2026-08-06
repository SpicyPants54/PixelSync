from pathlib import Path

from loguru import logger

from app.core.config import load_config
from app.core.database import create_database
from app.core.history import TransferHistory

from app.adb.adb_manager import ADBManager
from app.adb.transfer import TransferManager

from app.importer.queue import TransferQueue
from app.importer.folder_watcher import FolderWatcher
from app.importer.processor import QueueProcessor
from app.adb.device_monitor import DeviceMonitor

class PixelSyncApp:

    def __init__(self):

        self.config = load_config()

        self.queue = TransferQueue()

        self.adb = ADBManager()

        self.database = create_database(
            self.config.database_file
        )

        session = self.database()

        self.history = TransferHistory(
            session
        )

        self.transfer = None

        self.watcher = None

        self.processor = None


    def start(self):

        logger.info(
            "PixelSync starting..."
        )


        #
        # Start folder watcher
        #
        self.watcher = FolderWatcher(
            self.config.import_folder,
            self.queue
        )

        self.watcher.start()


        #
        # Connect Pixel
        #
        self.adb.check_adb()

        device = self.adb.connect()


        logger.info(
            f"Device model: {device}"
        )

        self.device_monitor = DeviceMonitor(
          self.adb
        )

        self.device_monitor.start()

        #
        # Create transfer engine
        #
        self.transfer = TransferManager(
            self.adb.device
        )


        #
        # Start queue processor
        #
        self.processor = QueueProcessor(
            self.queue,
            self.transfer,
            self.history
        )

        self.processor.start()


        logger.info(
            "Transfer engine ready"
        )


        logger.info(
            "PixelSync ready"
        )


        #
        # Keep application alive
        #
        import time

        while True:

            time.sleep(60)