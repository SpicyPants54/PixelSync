import threading
import time
from pathlib import Path

from loguru import logger

from app.importer.hash import calculate_hash
from app.importer.bundle_builder import build_bundle


class TransferQueue:

    def __init__(
        self,
        session=None
    ):
        self.session = session

        self.items = []

        self.lock = threading.Lock()

    def add(
        self,
        file
    ):
        file = Path(file)

        with self.lock:

            if file not in self.items:

                self.items.append(file)

                logger.info(
                    f"Added to transfer queue: "
                    f"{file.name}"
                )

    def get_next(self):

        with self.lock:

            if not self.items:

                return None

            return self.items.pop(0)

    def fail(
        self,
        file
    ):
        logger.warning(
            f"Transfer failed: "
            f"{Path(file).name}"
        )

    def complete(
        self,
        file
    ):
        logger.info(
            f"Transfer complete: "
            f"{Path(file).name}"
        )


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

    def wait_for_file_ready(
        self,
        file_path,
        checks=3,
        delay=1
    ):
        file_path = Path(file_path)

        logger.info(
            f"Checking file stability: "
            f"{file_path.name}"
        )

        last_size = -1
        stable_count = 0

        while stable_count < checks:

            if not file_path.exists():

                logger.warning(
                    f"File disappeared: "
                    f"{file_path.name}"
                )

                return False

            try:

                current_size = (
                    file_path.stat().st_size
                )

            except Exception as error:

                logger.error(
                    f"File size check failed: "
                    f"{error}"
                )

                return False

            if current_size == last_size:

                stable_count += 1

            else:

                stable_count = 0

                logger.info(
                    f"File still changing: "
                    f"{file_path.name} "
                    f"({current_size} bytes)"
                )

            last_size = current_size

            time.sleep(delay)

        logger.info(
            f"File ready: {file_path.name}"
        )

        return True

    def get_destination(
        self,
        media
    ):
        destination = (
            self.transfer.config.pixel_folder
        )

        logger.debug(
            f"Destination selected for "
            f"{media.name}: {destination}"
        )

        return destination

    def run(self):

        while self.running:

            file = self.queue.get_next()

            if not file:

                time.sleep(1)

                continue

            logger.info(
                f"Processing: {file.name}"
            )

            if not self.wait_for_file_ready(
                file
            ):

                logger.warning(
                    f"Skipping unstable file: "
                    f"{file.name}"
                )

                self.queue.fail(file)

                continue

            bundle = build_bundle(
                file,
                self.import_folder
            )

            logger.info(
                f"Bundle size: {len(bundle)}"
            )

            failed = False

            for media in bundle:

                file_hash = calculate_hash(
                    media
                )

                if self.history.exists(
                    file_hash
                ):

                    logger.info(
                        f"Skipping duplicate: "
                        f"{media.name}"
                    )

                    continue

                destination = (
                    self.get_destination(
                        media
                    )
                )

                logger.info(
                    f"Transfer destination: "
                    f"{destination}"
                )

                start_time = time.time()

                success = (
                    self.transfer.push_file(
                        media,
                        destination=destination
                    )
                )

                duration = (
                    time.time()
                    -
                    start_time
                )

                if success:

                    self.history.add(
                        filename=media.name,
                        file_hash=file_hash,
                        size=media.stat().st_size,
                        device=self.transfer.adb.device,
                        transport=(
                            self.transfer.adb
                            .get_transport()
                        ),
                        duration=duration
                    )

                    logger.info(
                        f"Transfer recorded: "
                        f"{media.name} "
                        f"{duration:.2f}s"
                    )

                else:

                    failed = True

                    logger.error(
                        f"Transfer failed: "
                        f"{media.name}"
                    )

            if failed:

                self.queue.fail(
                    file
                )

            else:

                self.queue.complete(
                    file
                )