from pathlib import Path
from loguru import logger


class MediaBundler:


    def __init__(self):

        self.pending = {}



    def add(self, file):

        file = Path(file)

        key = file.stem


        if key not in self.pending:

            self.pending[key] = []


        self.pending[key].append(file)


        logger.info(
            f"Bundle candidate: {key}"
        )


    def get(self, key):

        return self.pending.get(key)