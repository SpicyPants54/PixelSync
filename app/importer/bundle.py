from pathlib import Path


class MediaBundle:

    def __init__(
        self,
        photo=None,
        video=None
    ):

        self.photo = photo
        self.video = video


    def files(self):

        result = []

        if self.photo:
            result.append(self.photo)

        if self.video:
            result.append(self.video)

        return result