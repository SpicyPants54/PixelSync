from loguru import logger

from app.core.settings import Settings
from app.core.database import create_database
from app.core.history import TransferHistory
from app.core.events import TransferEvents
from app.core.transfer_state import TransferState

from app.adb.adb_manager import ADBManager
from app.adb.transfer import TransferManager
from app.adb.device_monitor import DeviceMonitor

from app.importer.queue import TransferQueue
from app.importer.folder_watcher import FolderWatcher
from app.importer.processor import QueueProcessor



class PixelSyncApp:


    def __init__(self):

        self.config = Settings()


        #
        # Database
        #

        self.database = create_database(
            self.config.database_file
        )

        self.session = self.database()



        #
        # Event system
        #

        self.events = TransferEvents()


        #
        # Transfer state
        #

        self.state = TransferState()



        #
        # Queue / History
        #

        self.queue = TransferQueue(
            self.session
        )


        self.history = TransferHistory(
            self.session
        )



        #
        # ADB
        #

        self.adb = ADBManager(
            self.config
        )



        self.transfer = None
        self.watcher = None
        self.processor = None
        self.device_monitor = None



        #
        # Event bindings
        #

        self.events.subscribe(
            "started",
            self.on_transfer_started
        )


        self.events.subscribe(
            "progress",
            self.on_transfer_progress
        )


        self.events.subscribe(
            "finished",
            self.on_transfer_finished
        )


        self.events.subscribe(
            "failed",
            self.on_transfer_failed
        )




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
        # Pixel connection
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
        # Transfer engine
        #

        self.transfer = TransferManager(
            self.adb,
            self.config,
            self.events
        )



        #
        # Queue processor
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





    #
    # Event handlers
    #


    def on_transfer_started(
        self,
        **data
    ):

        filename = data.get(
            "filename"
        )


        logger.info(
            f"[STATE] Starting: {filename}"
        )


        self.state.start(
            filename=filename,
            device=data.get(
                "device",
                ""
            ),
            total_bytes=data.get(
                "size",
                0
            )
        )




    def on_transfer_progress(
        self,
        **data
    ):

        filename = data.get(
            "filename"
        )


        self.state.update(
            filename=filename,
            transferred_bytes=data.get(
                "transferred",
                0
            ),
            percent=data.get(
                "percent",
                0
            ),
            speed_mbps=data.get(
                "speed",
                0
            ),
            eta_seconds=data.get(
                "eta",
                0
            )
        )




    def on_transfer_finished(
        self,
        **data
    ):

        filename = data.get(
            "filename"
        )


        logger.info(
            f"[STATE] Finished: {filename}"
        )


        self.state.finish(
            filename
        )




    def on_transfer_failed(
        self,
        **data
    ):

        filename = data.get(
            "filename"
        )


        logger.warning(
            f"[STATE] Failed: {filename}"
        )


        self.state.fail(
            filename,
            data.get(
                "error",
                ""
            )
        )