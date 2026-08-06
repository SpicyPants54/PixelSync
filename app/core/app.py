from loguru import logger

from app.core.settings import Settings
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

        self.config = Settings()

        self.queue = TransferQueue()

        self.adb = ADBManager(
            self.config
        )


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

        self.device_monitor = None




    def start(self):

        logger.info(
            "PixelSync starting..."
        )



        self.watcher = FolderWatcher(
            self.config.import_folder,
            self.queue
        )


        self.watcher.start()



        #
        # Connect Pixel
        #

        self.adb.check_adb()

        self.adb.connect()



        logger.info(
            f"Device model: {self.adb.get_model()}"
        )



        self.device_monitor = DeviceMonitor(
            self.adb
        )


        self.device_monitor.start()



        #
        # Create transfer engine
        #

        self.transfer = TransferManager(
            self.adb,
            self.config
        )



        #
        # Start processor
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



        import time


        while True:

            time.sleep(60)