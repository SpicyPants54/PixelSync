from pathlib import Path

from app.adb.transfer import TransferManager


class FakeADB:

    adb_path = Path("adb")

    device = "HT8581A00764"


class FakeConfig:

    pixel_folder = "/storage/emulated/0/DCIM/Camera"

    retry_count = 1

    retry_delay = 0


class FakeProcess:

    returncode = 0

    def __init__(self):

        self.poll_results = [None, 0]

    def poll(self):

        return self.poll_results.pop(0)

    def communicate(self, timeout):

        return "", ""


def test_push_does_not_poll_remote_size_while_adb_is_active(
    monkeypatch,
    tmp_path,
):

    media = tmp_path / "photo.jpg"

    media.write_bytes(b"photo")

    manager = TransferManager(
        FakeADB(),
        FakeConfig(),
    )

    manager.wait_for_device_ready = lambda device: True

    manager.scan_media = lambda device, path: None

    manager.get_remote_file_size = lambda device, path: (
        (_ for _ in ()).throw(
            AssertionError(
                "Remote size polling must not run during adb push"
            )
        )
    )

    monkeypatch.setattr(
        "app.adb.transfer.subprocess.Popen",
        lambda *args, **kwargs: FakeProcess(),
    )

    monkeypatch.setattr(
        "app.adb.transfer.time.sleep",
        lambda seconds: None,
    )

    assert manager.push_file(media)
