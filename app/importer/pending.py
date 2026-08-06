from pathlib import Path
import time


class PendingMedia:

    def __init__(self):

        self.files = {}


    def add(self, file):

        file = Path(file)

        self.files[file.stem] = {
            "file": file,
            "time": time.time()
        }


    def get_pair(self, file):

        file = Path(file)

        return self.files.get(
            file.stem
        )


    def remove(self, key):

        if key in self.files:

            del self.files[key]