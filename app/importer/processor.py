import threading
import time
from pathlib import Path

from loguru import logger

from app.importer.hash import calculate_hash
from app.importer.bundle_builder import build_bundle


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

        self.import_folder = Path(
            r"C:\Users\mitch\Pictures\PixelSync Import"
        )

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

            if not file:

                time.sleep(1)
                continue


            logger.info(
                f"Processing: {file.name}"
            )


            # Allow companion files to arrive
            time.sleep(5)


            bundle = build_bundle(
                file,
                self.import_folder
            )


            logger.info(
                f"Bundle size: {len(bundle)}"
            )


            for media in bundle:

                file_hash = calculate_hash(
                    media
                )


                if self.history.exists(
                    file_hash
                ):

                    logger.info(
                        f"Skipping duplicate: {media.name}"
                    )

                    continue


                success = self.transfer.push_file(
                    media,
                )


                if success:

                    self.history.add(
                        media.name,
                        file_hash,
                        media.stat().st_size
                    )