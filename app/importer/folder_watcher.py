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



class FolderWatcher:

    def __init__(self, folder, queue):

        self.folder = folder
        self.queue = queue
        self.observer = Observer()


    def start(self):

        Path(self.folder).mkdir(
            parents=True,
            exist_ok=True
        )

        handler = ImportHandler(
            self.queue
        )

        self.observer.schedule(
            handler,
            self.folder,
            recursive=True
        )

        self.observer.start()

        logger.info(
            f"Watching folder recursively: {self.folder}"
        )