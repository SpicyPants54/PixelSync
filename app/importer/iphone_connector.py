import os
import subprocess
from pathlib import Path

from loguru import logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class IPhoneConnector:

    def __init__(
        self,
        tool_directory=None,
        command_runner=None
    ):

        configured_directory = (
            tool_directory
            or
            os.environ.get(
                "PIXELSYNC_LIBIMOBILEDEVICE_PATH"
            )
            or
            PROJECT_ROOT
            /
            "tools"
            /
            "libimobiledevice"
        )

        self.tool_directory = Path(
            configured_directory
        )

        self.command_runner = (
            command_runner
            or
            subprocess.run
        )

        self.udid = ""
        self.transport = ""


    def get_tool_path(
        self,
        name
    ):

        suffix = (
            ".exe"
            if os.name == "nt"
            else ""
        )

        return (
            self.tool_directory
            /
            f"{name}{suffix}"
        )


    def tools_available(self):

        required_tools = (
            "idevice_id",
            "ideviceinfo",
            "afcclient",
        )

        return all(
            self.get_tool_path(tool).is_file()
            for tool in required_tools
        )


    def _run(
        self,
        tool,
        *arguments,
        timeout=15
    ):

        executable = self.get_tool_path(
            tool
        )

        if not executable.is_file():

            logger.warning(
                f"iPhone tool is unavailable: "
                f"{executable}"
            )

            return None

        try:

            return self.command_runner(
                [
                    str(executable),
                    *arguments,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

        except (
            OSError,
            subprocess.SubprocessError
        ) as error:

            logger.warning(
                f"iPhone command failed: {error}"
            )

            return None


    def list_devices(
        self,
        transport
    ):

        if transport not in {
            "usb",
            "wifi",
        }:

            raise ValueError(
                "transport must be usb or wifi"
            )

        arguments = (
            ["--list"]
            if transport == "usb"
            else ["--network"]
        )

        result = self._run(
            "idevice_id",
            *arguments
        )

        if not result or result.returncode != 0:

            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]


    def connect(self):

        for transport in (
            "usb",
            "wifi",
        ):

            devices = self.list_devices(
                transport
            )

            if not devices:

                continue

            self.udid = devices[0]
            self.transport = transport

            logger.info(
                f"iPhone connected over "
                f"{transport}: {self.udid}"
            )

            return True

        self.udid = ""
        self.transport = ""

        return False


    def get_info(
        self,
        key=None
    ):

        if not self.udid:

            return None

        arguments = [
            "--udid",
            self.udid,
            "--simple",
        ]

        if self.transport == "wifi":

            arguments.append(
                "--network"
            )

        if key:

            arguments.extend(
                [
                    "--key",
                    key,
                ]
            )

        result = self._run(
            "ideviceinfo",
            *arguments
        )

        if not result or result.returncode != 0:

            return None

        output = result.stdout.strip()

        return output or None


    def get_model(self):

        return self.get_info(
            "ProductType"
        )


    def is_connected(self):

        if not self.udid or not self.transport:

            return False

        return self.udid in self.list_devices(
            self.transport
        )
