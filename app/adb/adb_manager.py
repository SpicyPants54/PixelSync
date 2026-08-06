import subprocess
from loguru import logger


class ADBManager:

    def __init__(self):
        self.device = None


    def check_adb(self):
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("ADB detected")
                return True

        except Exception as e:
            logger.error(
                f"ADB error: {e}"
            )

        return False


    def get_devices(self):

        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True
        )

        devices = []

        for line in result.stdout.splitlines():

            if "\tdevice" in line:
                serial = line.split("\t")[0]
                devices.append(serial)

        return devices


    def connect(self):

        devices = self.get_devices()

        if not devices:
            logger.warning(
                "No Pixel device found"
            )
            return False


        self.device = devices[0]

        logger.info(
            f"Pixel detected: {self.device}"
        )

        return True


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

        return result.stdout.strip()