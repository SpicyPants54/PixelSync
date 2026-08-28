from app.adb.device_monitor import DeviceMonitor


class FakeADB:

    def __init__(self):

        self.device = "192.168.1.38:5555"

        self.usb_device_calls = []

    def get_usb_device(self):

        return "HT8581A00764"

    def use_usb_device(self, device):

        self.usb_device_calls.append(device)

        self.device = device

    def get_transport(self):

        if ":" in self.device:

            return "wifi"

        return "usb"

    def get_model(self):

        return "Pixel 2"


def test_monitor_restores_usb_through_adb_manager(monkeypatch):

    adb = FakeADB()

    updates = []

    monitor = DeviceMonitor(
        adb,
        callback=lambda **data: updates.append(data),
    )

    def stop_after_usb_check(_):

        monitor.running = False

    monkeypatch.setattr(
        "app.adb.device_monitor.time.sleep",
        stop_after_usb_check,
    )

    monitor.running = True

    monitor.run()

    assert adb.usb_device_calls == ["HT8581A00764"]

    assert updates == [
        {
            "connected": True,
            "serial": "HT8581A00764",
            "model": "Pixel 2",
            "transport": "usb",
        }
    ]


def test_monitor_defers_usb_switch_while_wifi_transfer_is_active(
    monkeypatch,
):

    adb = FakeADB()

    updates = []

    transfer = type(
        "Transfer",
        (),
        {"active_transfer": True},
    )()

    monitor = DeviceMonitor(
        adb,
        callback=lambda **data: updates.append(data),
        transfer=transfer,
    )

    def stop_after_check(_):

        monitor.running = False

    monkeypatch.setattr(
        "app.adb.device_monitor.time.sleep",
        stop_after_check,
    )

    monitor.running = True

    monitor.run()

    assert adb.usb_device_calls == []

    assert updates == [
        {
            "connected": True,
            "serial": "192.168.1.38:5555",
            "model": "Pixel 2",
            "transport": "wifi",
        }
    ]
