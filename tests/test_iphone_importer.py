from pathlib import Path, PurePosixPath
from types import SimpleNamespace

from app.importer.iphone_importer import IPhoneImporter


class FakeAFC:

    files = []
    downloads = []

    def __init__(
        self,
        tool_directory,
        udid,
        transport
    ):

        self.arguments = (
            tool_directory,
            udid,
            transport,
        )

    def __enter__(self):

        return self

    def __exit__(
        self,
        exception_type,
        exception,
        traceback
    ):

        return None

    def walk_media(self):

        yield from self.files

    def download(
        self,
        remote_path,
        destination
    ):

        destination = Path(
            destination
        )

        size = dict(
            self.files
        )[remote_path]["st_size"]

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        destination.write_bytes(
            b"x" * int(size)
        )

        self.downloads.append(
            (
                remote_path,
                destination,
            )
        )


def make_importer(
    tmp_path
):

    connector = SimpleNamespace(
        udid="iphone-id",
        transport="wifi",
        tool_directory=tmp_path,
        connect=lambda: True
    )

    return IPhoneImporter(
        connector,
        tmp_path / "import",
        afc_factory=FakeAFC
    )


def test_sync_downloads_into_device_scoped_folder(
    tmp_path
):

    FakeAFC.files = [
        (
            PurePosixPath(
                "/DCIM/100APPLE/IMG_0001.HEIC"
            ),
            {
                "st_size": "4",
            },
        ),
    ]

    FakeAFC.downloads = []

    importer = make_importer(
        tmp_path
    )

    summary = importer.sync()

    destination = (
        tmp_path
        /
        "import"
        /
        "iPhone"
        /
        "iphone-id"
        /
        "100APPLE"
        /
        "IMG_0001.HEIC"
    )

    assert destination.read_bytes() == b"xxxx"
    assert summary == {
        "discovered": 1,
        "downloaded": 1,
        "skipped": 0,
        "failed": 0,
    }


def test_sync_skips_file_with_matching_size(
    tmp_path
):

    FakeAFC.files = [
        (
            PurePosixPath(
                "/DCIM/100APPLE/IMG_0002.JPG"
            ),
            {
                "st_size": "3",
            },
        ),
    ]

    FakeAFC.downloads = []

    importer = make_importer(
        tmp_path
    )

    destination = importer.get_destination(
        FakeAFC.files[0][0],
        3
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.write_bytes(
        b"old"
    )

    summary = importer.sync()

    assert summary["skipped"] == 1
    assert FakeAFC.downloads == []


def test_size_collision_uses_distinct_filename(
    tmp_path
):

    importer = make_importer(
        tmp_path
    )

    remote_path = PurePosixPath(
        "/DCIM/100APPLE/IMG_0003.JPG"
    )

    original = importer.get_destination(
        remote_path,
        3
    )

    original.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    original.write_bytes(
        b"old"
    )

    collision = importer.get_destination(
        remote_path,
        4
    )

    assert collision.name == (
        "IMG_0003-4.JPG"
    )
