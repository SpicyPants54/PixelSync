from pathlib import Path


class MediaBundle:

    def __init__(
        self,
        files=None
    ):

        self._files = []

        if files:

            for file in files:

                self._files.append(
                    Path(file)
                )


    def files(self):

        return list(
            self._files
        )


    def add(
        self,
        file
    ):

        file = Path(file)

        if file not in self._files:

            self._files.append(
                file
            )


    def __len__(self):

        return len(
            self._files
        )


    def __iter__(self):

        return iter(
            self._files
        )