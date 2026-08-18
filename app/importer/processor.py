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

    def stop(self):

        self.running = False

        logger.info(
            "Queue processor stopped"
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

    def get_import_folder(self):

        folder = Path(
            self.transfer.config.import_folder
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return folder

    def get_destination(
        self,
        media
    ):
        """
        Determine the Android destination
        for a media file.

        Organization routing will eventually
        be handled here.

        For now, all media continues to use
        the configured Pixel destination.
        """

        destination = (
            self.transfer.config.pixel_folder
        )

        logger.debug(
            f"Destination selected for "
            f"{media.name}: {destination}"
        )

        return destination

    def process_file(
        self,
        file
    ):

        file = Path(file)

        logger.info(
            f"Processing: {file.name}"
        )

        if not self.wait_for_file_ready(file):

            logger.warning(
                f"Skipping unstable file: "
                f"{file.name}"
            )

            self.queue.fail(file)

            return

        import_folder = (
            self.get_import_folder()
        )

        bundle = build_bundle(
            file,
            import_folder
        )

        logger.info(
            f"Bundle size: {len(bundle)}"
        )

        failed = False

        for media in bundle:

            media = Path(media)

            if not media.exists():

                logger.warning(
                    f"Media file disappeared: "
                    f"{media.name}"
                )

                failed = True

                continue

            try:

                file_hash = calculate_hash(
                    media
                )

            except Exception as error:

                logger.error(
                    f"Hash calculation failed "
                    f"for {media.name}: {error}"
                )

                failed = True

                continue

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

            try:

                success = (
                    self.transfer.push_file(
                        media,
                        destination=destination
                    )
                )

            except Exception as error:

                logger.exception(
                    f"Transfer exception for "
                    f"{media.name}: {error}"
                )

                success = False

            duration = (
                time.time()
                -
                start_time
            )

            if success:

                try:

                    device = (
                        self.transfer.adb.device
                    )

                except Exception:

                    device = ""

                try:

                    transport = (
                        self.transfer.adb
                        .get_transport()
                    )

                except Exception:

                    transport = ""

                self.history.add(
                    filename=media.name,
                    file_hash=file_hash,
                    size=media.stat().st_size,
                    device=device,
                    transport=transport,
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

            self.queue.fail(file)

        else:

            self.queue.complete(file)

    def run(self):

        while self.running:

            try:

                file = self.queue.get_next()

            except Exception as error:

                logger.exception(
                    f"Queue error: {error}"
                )

                time.sleep(1)

                continue

            if not file:

                time.sleep(1)

                continue

            try:

                self.process_file(file)

            except Exception as error:

                logger.exception(
                    f"Unexpected processor error "
                    f"for {file}: {error}"
                )

                self.queue.fail(file)