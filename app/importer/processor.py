import threading
import time

from loguru import logger

from app.importer.hash import calculate_hash


class QueueProcessor:

    def __init__(
        self,
        queue,
        transfer,
        history
    ):

        self.queue = queue
        self.transfer = transfer
        self.history = history

        self.running = False


    def start(self):

        self.running = True

        thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        thread.start()

        logger.info(
            "Queue processor started"
        )


    def run(self):

        while self.running:

            file = self.queue.get_next()

            if file:

                logger.info(
                    f"Processing: {file.name}"
                )


                file_hash = calculate_hash(
                    file
                )


                if self.history.exists(
                    file_hash
                ):

                    logger.info(
                        f"Skipping duplicate: {file.name}"
                    )

                    continue


                success = self.transfer.push_file(
                    file,
                    "/storage/emulated/0/DCIM/Camera/"
                )


                if success:

                    self.history.add(
                        file.name,
                        file_hash,
                        file.stat().st_size
                    )

            else:

                time.sleep(1)