from types import SimpleNamespace

from app.adb.adb_manager import ADBManager
from app.core.transfer_state import TransferState


def test_storage_info_parses_android_df_output():

    manager = ADBManager(
        SimpleNamespace()
    )

    manager.device = "HT8581A00764"

    manager._run_adb = lambda *args, **kwargs: SimpleNamespace(
        returncode=0,
        stdout=(
            "Filesystem 1K-blocks Used Available Use% Mounted on\n"
            "/dev/fuse 62552436 20000000 42552436 32% "
            "/storage/emulated/0\n"
        ),
    )

    assert manager.get_storage_info() == {
        "total_bytes": 62552436 * 1024,
        "used_bytes": 20000000 * 1024,
        "free_bytes": 42552436 * 1024,
        "used_percent": 32,
    }


def test_transfer_state_exposes_storage_cleanup_recommendation():

    state = TransferState()

    state.device_connected(
        serial="HT8581A00764",
        storage={
            "total_bytes": 64 * 1024,
            "used_bytes": 60 * 1024,
            "free_bytes": 4 * 1024,
            "used_percent": 94,
        },
        storage_cleanup_recommended=True,
    )

    snapshot = state.get_snapshot()

    assert snapshot["storage_free_bytes"] == 4 * 1024

    assert snapshot["storage_cleanup_recommended"] is True

    state.device_disconnected()

    assert state.get_snapshot()["storage_free_bytes"] == 0
