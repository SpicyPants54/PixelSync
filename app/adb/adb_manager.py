import subprocess

from loguru import logger

from app.adb.device_store import DeviceStore


class ADBManager:

    def __init__(self, config):

        self.config = config
        self.device = None
        self.device_store = DeviceStore()



    def check_adb(self):

        try:

            result = subprocess.run(
                [
                    "adb",
                    "version"
                ],
                capture_output=True,
                text=True
            )


            if result.returncode == 0:

                logger.info(
                    "ADB detected"
                )

                return True


        except Exception as error:

            logger.error(
                f"ADB error: {error}"
            )


        return False



    def get_devices(self):

        try:

            result = subprocess.run(
                [
                    "adb",
                    "devices"
                ],
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

                serial = line.split("\t")[0]

                devices.append(serial)


        return devices



    def get_usb_device(self):

        devices = self.get_devices()


        for device in devices:

            if ":" not in device:

                return device


        return None



    def connect(self):

        usb_device = self.get_usb_device()


        #
        # USB always wins
        #
        if usb_device:

            self.device = usb_device


            self.device_store.update_device(
                serial=usb_device,
                transport="usb"
            )


            logger.info(
                f"Using USB Pixel: {usb_device}"
            )


            self.learn_wifi_address()


            return True



        #
        # WiFi fallback
        #
        if self.config.wifi_fallback:

            return self.connect_wifi()



        self.device = None


        logger.warning(
            "No Pixel device found"
        )


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


        output = (
            result.stdout.lower()
            +
            result.stderr.lower()
        )


        if (
            "connected" in output
            or
            "already connected" in output
        ):

            self.device = address


            stored = self.device_store.find_by_wifi(
                self.config.wifi_address
            )


            if stored:

                serial = stored.get(
                    "serial"
                )

            else:

                serial = address



            self.device_store.update_device(
                serial=serial,
                wifi_address=self.config.wifi_address,
                transport="wifi"
            )


            logger.info(
                f"Using WiFi Pixel: {address}"
            )


            return True



        logger.warning(
            "WiFi Pixel connection failed"
        )


        return False



    def disconnect_wifi(self):

        if not self.device:

            return


        if ":" not in self.device:

            return


        try:

            subprocess.run(
                [
                    "adb",
                    "disconnect",
                    self.device
                ],
                capture_output=True,
                text=True
            )


            logger.info(
                f"Disconnected WiFi Pixel: {self.device}"
            )


        except Exception as error:

            logger.error(
                f"WiFi disconnect failed: {error}"
            )



    def is_connected(self):

        devices = self.get_devices()


        return (
            self.device is not None
            and self.device in devices
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


        return result.stdout.strip()



    def get_transport(self):

        if not self.device:

            return None


        if ":" in self.device:

            return "wifi"


        return "usb"



    def learn_wifi_address(self):

        if self.get_transport() != "usb":

            return False


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


                    if not ip.startswith("192."):

                        continue



                    if self.config.wifi_address != ip:

                        self.config.set_wifi_address(
                            ip
                        )


                        logger.info(
                            f"Saved WiFi Pixel address: {ip}"
                        )


                    self.device_store.update_device(
                        serial=self.device,
                        wifi_address=ip,
                        transport="usb"
                    )


                    return True



        except Exception as error:

            logger.error(
                f"WiFi learning failed: {error}"
            )


        return False