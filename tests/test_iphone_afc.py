from pathlib import PurePosixPath

from app.importer.iphone_afc import IPhoneAFC


class FakeAFC(IPhoneAFC):

    def __init__(self):

        self.directories = {
            PurePosixPath("/DCIM"): [
                "100APPLE",
                "notes.txt",
            ],
            PurePosixPath("/DCIM/100APPLE"): [
                "IMG_0001.HEIC",
                "IMG_0001.MOV",
                "metadata.dat",
            ],
        }

        self.information = {
            PurePosixPath("/DCIM/100APPLE"): {
                "st_ifmt": "S_IFDIR",
            },
            PurePosixPath("/DCIM/notes.txt"): {
                "st_ifmt": "S_IFREG",
            },
            PurePosixPath(
                "/DCIM/100APPLE/IMG_0001.HEIC"
            ): {
                "st_ifmt": "S_IFREG",
                "st_size": "100",
            },
            PurePosixPath(
                "/DCIM/100APPLE/IMG_0001.MOV"
            ): {
                "st_ifmt": "S_IFREG",
                "st_size": "200",
            },
            PurePosixPath(
                "/DCIM/100APPLE/metadata.dat"
            ): {
                "st_ifmt": "S_IFREG",
            },
        }

    def list_directory(
        self,
        remote_path
    ):

        return self.directories[
            PurePosixPath(
                remote_path
            )
        ]

    def get_file_info(
        self,
        remote_path
    ):

        return self.information[
            PurePosixPath(
                remote_path
            )
        ]


def test_walk_media_recurses_and_filters_extensions():

    afc = FakeAFC()

    media = list(
        afc.walk_media()
    )

    assert [
        path
        for path, _ in media
    ] == [
        PurePosixPath(
            "/DCIM/100APPLE/IMG_0001.HEIC"
        ),
        PurePosixPath(
            "/DCIM/100APPLE/IMG_0001.MOV"
        ),
    ]


def test_afc_rejects_unknown_transport(
    tmp_path
):

    try:

        IPhoneAFC(
            tmp_path,
            "device",
            transport="bluetooth"
        )

    except ValueError as error:

        assert "usb or wifi" in str(
            error
        )

    else:

        raise AssertionError(
            "Expected ValueError"
        )
