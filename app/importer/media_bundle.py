from pathlib import Path


class MediaBundle:

    def __init__(
        self,
        files
    ):

        self.files = [
            Path(file)
            for file in files
        ]


    def add(self, file):

        file = Path(file)

        if file not in self.files:

            self.files.append(
                file
            )


    def __iter__(self):

        return iter(
            self.files
        )


    def __len__(self):

        return len(
            self.files
        )