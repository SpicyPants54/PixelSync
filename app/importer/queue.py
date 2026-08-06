from queue import Queue
from loguru import logger


class TransferQueue:

    def __init__(self):

        self.queue = Queue()


    def add(self, file_path):

        logger.info(
            f"Queued: {file_path}"
        )

        self.queue.put(file_path)


    def get_next(self):

        if not self.queue.empty():

            return self.queue.get()

        return None


    def size(self):

        return self.queue.qsize()