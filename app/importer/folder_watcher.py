from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger
from pathlib import Path
import time


MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".mov",
    ".mp4"
}


class ImportHandler(FileSystemEventHandler):

    def __init__(self, queue):
        self.queue = queue

    def on_created(self, event):

        logger.info(
            f"Filesystem event: {event.src_path}"
        )

        if event.is_directory:
            return

        file = Path(event.src_path)

        if file.suffix.lower() in MEDIA_EXTENSIONS:

            logger.info(
                f"New media detected: {file.name}"
            )

            self.queue.add(file)

    def on_moved(self, event):

        if event.is_directory:
            return

        file = Path(event.dest_path)

        if file.suffix.lower() in MEDIA_EXTENSIONS:

            logger.info(
                f"Media moved into import folder: {file.name}"
            )

            self.queue.add(file)


class FolderWatcher:

    def __init__(self, folder, queue):

        self.folder = Path(folder)
        self.queue = queue
        self.observer = Observer()

    def scan_existing_files(self):

        logger.info(
            f"Scanning existing media: {self.folder}"
        )

        if not self.folder.exists():

            logger.warning(
                f"Import folder does not exist: {self.folder}"
            )

            return

        files = []

        try:

            for file in self.folder.rglob("*"):

                if not file.is_file():
                    continue

                if file.suffix.lower() not in MEDIA_EXTENSIONS:
                    continue

                files.append(file)

        except Exception as error:

            logger.exception(
                f"Failed to scan import folder: {error}"
            )

            return

        logger.info(
            f"Existing media scan found {len(files)} file(s)"
        )

        for file in sorted(files):

            logger.info(
                f"Queuing existing media: {file.name}"
            )

            self.queue.add(file)

    def start(self):

        self.folder.mkdir(
            parents=True,
            exist_ok=True
        )

        handler = ImportHandler(
            self.queue
        )

        self.observer.schedule(
            handler,
            str(self.folder),
            recursive=True
        )

        self.observer.start()

        logger.info(
            f"Watching folder recursively: {self.folder}"
        )

        # Give the filesystem watcher a moment to initialize
        # before scanning existing files. This prevents a file
        # created during startup from being missed.
        time.sleep(0.25)

        self.scan_existing_files()

    def stop(self):

        logger.info(
            "Stopping folder watcher"
        )

        self.observer.stop()
        self.observer.join()

        logger.info(
            "Folder watcher stopped"
        )