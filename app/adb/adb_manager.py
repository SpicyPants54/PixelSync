import subprocess
import json

from pathlib import Path
from loguru import logger


class ADBManager:

    def __init__(self, config):

        self.config = config
        self.device = None
        self.transport = None
        self.model = None


    def check_adb(self):

        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return True

        except Exception as error:
            logger.error(
                f"ADB error: {error}"
            )

        return False


    def get_devices(self):

        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
            )

        except Exception as error:
            logger.error(
                f"ADB device query failed: {error}"
            )
            return []


        devices = []

        for line in result.stdout.splitlines():

            if "\tdevice" in line:

                devices.append(
                    line.split("\t")[0]
                )

        return devices


    def connect(self):

        devices = self.get_devices()


        for device in devices:

            if ":" not in device:

                self.device = device
                self.transport = "usb"

                logger.info(
                    f"Using USB Pixel: {device}"
                )

                self.learn_wifi_address()

                return True


        if self.config.wifi_fallback:

            return self.connect_wifi()


        self.device = None

        return False


    def connect_wifi(self):

        if not self.config.wifi_address:

            logger.warning(
                "No saved WiFi Pixel address"
            )

            return False


        address = (
            f"{self.config.wifi_address}:"
            f"{self.config.wifi_port}"
        )


        result = subprocess.run(
            [
                "adb",
                "connect",
                address
            ],
            capture_output=True,
            text=True
        )


        if "connected" in result.stdout.lower():

            self.device = address
            self.transport = "wifi"

            logger.info(
                f"Using WiFi Pixel: {address}"
            )

            return True


        return False


    def learn_wifi_address(self):

        if not self.device:
            return


        try:

            result = subprocess.run(
                [
                    "adb",
                    "-s",
                    self.device,
                    "shell",
                    "ip",
                    "addr",
                    "show",
                    "wlan0"
                ],
                capture_output=True,
                text=True
            )


            for line in result.stdout.splitlines():

                if "inet " in line:

                    ip = (
                        line.strip()
                        .split()[1]
                        .split("/")[0]
                    )


                    if ip.startswith("192."):

                        self.config.save_wifi_address(ip)

                        logger.info(
                            f"Saved WiFi Pixel address: {ip}"
                        )

                        return


        except Exception as error:

            logger.debug(
                f"WiFi discovery failed: {error}"
            )


    def is_connected(self):

        return (
            self.device in self.get_devices()
            if self.device
            else False
        )


    def get_model(self):

        if not self.device:
            return None


        result = subprocess.run(
            [
                "adb",
                "-s",
                self.device,
                "shell",
                "getprop",
                "ro.product.model"
            ],
            capture_output=True,
            text=True
        )


        self.model = result.stdout.strip()

        return self.model


    def get_transport(self):

        return self.transport