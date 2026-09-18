from pathlib import Path
from types import SimpleNamespace

from app.importer.iphone_connector import IPhoneConnector


def make_connector(
    tmp_path,
    responses
):

    for tool in (
        "idevice_id",
        "ideviceinfo",
        "afcclient",
    ):

        (tmp_path / f"{tool}.exe").touch()

    calls = []

    def run(
        command,
        **options
    ):

        calls.append(
            (command, options)
        )

        return responses.pop(0)

    connector = IPhoneConnector(
        tool_directory=tmp_path,
        command_runner=run
    )

    return connector, calls


def result(
    stdout="",
    returncode=0
):

    return SimpleNamespace(
        stdout=stdout,
        stderr="",
        returncode=returncode
    )


def test_connector_prefers_usb_over_wifi(
    tmp_path
):

    connector, calls = make_connector(
        tmp_path,
        [
            result(
                "usb-device\n"
            ),
        ]
    )

    assert connector.connect() is True
    assert connector.udid == "usb-device"
    assert connector.transport == "usb"
    assert calls[0][0][1:] == [
        "--list"
    ]
    assert len(calls) == 1


def test_connector_falls_back_to_wifi(
    tmp_path
):

    connector, calls = make_connector(
        tmp_path,
        [
            result(),
            result(
                "wifi-device\n"
            ),
            result(
                "iPhone18,1\n"
            ),
        ]
    )

    assert connector.connect() is True
    assert connector.transport == "wifi"
    assert connector.get_model() == "iPhone18,1"

    info_command = calls[2][0]

    assert info_command[1:] == [
        "--udid",
        "wifi-device",
        "--simple",
        "--network",
        "--key",
        "ProductType",
    ]


def test_connector_clears_stale_device_when_disconnected(
    tmp_path
):

    connector, _ = make_connector(
        tmp_path,
        [
            result(),
            result(),
        ]
    )

    connector.udid = "old-device"
    connector.transport = "usb"

    assert connector.connect() is False
    assert connector.udid == ""
    assert connector.transport == ""


def test_connector_requires_all_tools(
    tmp_path
):

    (tmp_path / "idevice_id.exe").touch()

    connector = IPhoneConnector(
        tool_directory=Path(tmp_path)
    )

    assert connector.tools_available() is False
