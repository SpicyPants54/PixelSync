from app.importer.iphone_monitor import IPhoneImportMonitor


class FakeImporter:

    def __init__(self):

        self.limits = []

    def sync(
        self,
        max_files=None
    ):

        self.limits.append(
            max_files
        )

        return {
            "discovered": 2,
            "downloaded": 1,
            "skipped": 1,
            "failed": 0,
        }


def test_monitor_applies_per_cycle_limit():

    importer = FakeImporter()

    monitor = IPhoneImportMonitor(
        importer,
        poll_interval=1,
        max_files_per_cycle=3
    )

    summary = monitor.sync_once()

    assert importer.limits == [
        3
    ]

    assert summary["downloaded"] == 1


def test_monitor_enforces_safe_minimums():

    monitor = IPhoneImportMonitor(
        FakeImporter(),
        poll_interval=0,
        max_files_per_cycle=0
    )

    assert monitor.poll_interval == 5
    assert monitor.max_files_per_cycle == 1
