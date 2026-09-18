import threading

from loguru import logger


class IPhoneImportMonitor:

    def __init__(
        self,
        importer,
        poll_interval=60,
        max_files_per_cycle=10
    ):

        self.importer = importer
        self.poll_interval = max(
            5,
            int(poll_interval)
        )

        self.max_files_per_cycle = max(
            1,
            int(max_files_per_cycle)
        )

        self.running = False
        self.thread = None
        self.stop_event = threading.Event()


    def sync_once(self):

        try:

            summary = self.importer.sync(
                max_files=(
                    self.max_files_per_cycle
                )
            )

            if summary["downloaded"]:

                logger.info(
                    "iPhone import cycle: "
                    f"{summary}"
                )

            return summary

        except Exception as error:

            logger.warning(
                f"iPhone import cycle failed: "
                f"{error}"
            )

            return {
                "discovered": 0,
                "downloaded": 0,
                "skipped": 0,
                "failed": 1,
            }


    def run(self):

        while not self.stop_event.is_set():

            self.sync_once()

            self.stop_event.wait(
                self.poll_interval
            )


    def start(self):

        if self.running:

            return

        self.running = True
        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        self.thread.start()

        logger.info(
            "iPhone import monitor started"
        )


    def stop(self):

        if not self.running:

            return

        self.running = False
        self.stop_event.set()

        if self.thread:

            self.thread.join(
                timeout=5
            )

        self.thread = None

        logger.info(
            "iPhone import monitor stopped"
        )
