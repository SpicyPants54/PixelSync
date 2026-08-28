from pathlib import Path
import subprocess
import time

from loguru import logger

from app.adb.device_store import DeviceStore


class ADBManager:

    def __init__(
        self,
        config
    ):

        self.config = config

        #
        # Current active ADB target.
        #
        # USB example:
        # HT8581A00764
        #
        # WiFi example:
        # 192.168.1.38:5555
        #

        self.device = None

        #
        # Physical device serial.
        #
        # Keep this separate from self.device because
        # self.device changes when switching between
        # USB and WiFi.
        #

        self.device_serial = ""

        self.device_store = DeviceStore()


        #
        # PixelSync ships with its own copy of ADB.
        #

        self.adb_path = (
            Path(__file__).resolve()
            .parents[2]
            / "tools"
            / "adb"
            / "adb.exe"
        )


        if not self.adb_path.exists():

            logger.error(
                f"Bundled ADB not found: "
                f"{self.adb_path}"
            )

        else:

            logger.debug(
                f"Using bundled ADB: "
                f"{self.adb_path}"
            )


    #
    # Internal ADB helper
    #

    def _run_adb(
        self,
        *args,
        timeout=15
    ):

        try:

            return subprocess.run(
                [
                    str(self.adb_path),
                    *args
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )

        except subprocess.TimeoutExpired:

            logger.warning(
                f"ADB command timed out: "
                f"{' '.join(args)}"
            )

        except Exception as error:

            logger.error(
                f"ADB command failed: {error}"
            )

        return None


    #
    # Check ADB
    #

    def check_adb(self):

        if not self.adb_path.exists():

            logger.error(
                f"Bundled ADB executable not found: "
                f"{self.adb_path}"
            )

            return False


        result = self._run_adb(
            "version"
        )


        if not result:

            return False


        if result.returncode == 0:

            logger.info(
                f"ADB detected: "
                f"{self.adb_path}"
            )

            return True


        logger.error(
            f"ADB check failed: "
            f"{result.stderr.strip()}"
        )

        return False


    #
    # Device discovery
    #

    def get_devices(self):

        result = self._run_adb(
            "devices"
        )


        if not result:

            return []


        devices = []


        for line in result.stdout.splitlines():

            line = line.strip()


            if not line:

                continue


            if line.startswith(
                "List of devices attached"
            ):

                continue


            parts = line.split()


            if len(parts) < 2:

                continue


            serial = parts[0]
            status = parts[1]


            if status == "device":

                devices.append(
                    serial
                )


        return devices


    def get_usb_device(self):

        devices = self.get_devices()


        for device in devices:

            #
            # Network ADB devices contain an address
            # and port, for example:
            #
            # 192.168.1.38:5555
            #

            if ":" not in device:

                return device


        return None


    def get_wifi_device(self):

        devices = self.get_devices()


        for device in devices:

            if ":" in device:

                return device


        return None


    #
    # Connection management
    #

    def connect(self):

        #
        # USB always wins.
        #

        usb_device = self.get_usb_device()


        if usb_device:

            return self.use_usb_device(
                usb_device
            )


        #
        # WiFi fallback.
        #

        if self.config.wifi_fallback:

            return self.connect_wifi()


        self.device = None


        logger.warning(
            "No Pixel device found"
        )

        return False


    def use_usb_device(
        self,
        usb_device
    ):

        previous_device = self.device


        self.device = usb_device
        self.device_serial = usb_device


        #
        # If we were using WiFi before, disconnect it.
        #

        if (
            previous_device
            and
            ":" in previous_device
            and
            previous_device != usb_device
        ):

            self.disconnect_wifi(
                previous_device
            )


        self.device_store.update_device(
            serial=usb_device,
            transport="usb"
        )


        logger.info(
            f"Using USB Pixel: {usb_device}"
        )


        #
        # Learn the current WiFi address.
        #

        self.learn_wifi_address()


        #
        # Prepare ADB-over-WiFi while USB is available.
        #
        # This is the critical step that was missing.
        #

        if self.config.wifi_fallback:

            self.enable_wifi_adb()


        return True


    #
    # Enable TCP/IP ADB
    #

    def enable_wifi_adb(self):

        if self.get_transport() != "usb":

            logger.debug(
                "Skipping WiFi ADB enable: "
                "USB device is not active"
            )

            return False


        if not self.config.wifi_address:

            logger.warning(
                "Cannot enable WiFi ADB: "
                "Pixel WiFi address is unknown"
            )

            return False


        port = str(
            self.config.wifi_port
        )


        logger.info(
            f"Enabling ADB TCP/IP on port {port}"
        )


        result = self._run_adb(
            "-s",
            self.device,
            "tcpip",
            port,
            timeout=20
        )


        if not result:

            return False


        output = (
            result.stdout.lower()
            +
            result.stderr.lower()
        )


        if (
            result.returncode != 0
            or
            "restarting in tcp mode"
            not in output
        ):

            logger.warning(
                f"Unable to enable WiFi ADB: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

            return False


        logger.info(
            f"ADB TCP/IP enabled on port {port}"
        )


        #
        # Give adbd a moment to restart in TCP mode.
        #

        time.sleep(
            1
        )


        #
        # Verify that we can actually connect over WiFi
        # before relying on it as a fallback.
        #

        if self.verify_wifi_connection():

            logger.info(
                "WiFi ADB verified and ready "
                "for USB fallback"
            )

            #
            # Return to USB as the active transfer path.
            #

            usb_device = self.get_usb_device()


            if usb_device:

                self.device = usb_device
                self.device_serial = usb_device


                logger.info(
                    f"Restored USB as active device: "
                    f"{usb_device}"
                )

            return True


        logger.warning(
            "WiFi ADB was enabled but could not "
            "be verified"
        )

        return False


    #
    # Verify WiFi connection while USB remains active
    #

    def verify_wifi_connection(self):

        if not self.config.wifi_address:

            return False


        address = (
            f"{self.config.wifi_address}:"
            f"{self.config.wifi_port}"
        )


        logger.info(
            f"Verifying WiFi ADB connection: "
            f"{address}"
        )


        result = self._run_adb(
            "connect",
            address,
            timeout=15
        )


        if not result:

            return False


        output = (
            result.stdout.lower()
            +
            result.stderr.lower()
        )


        if (
            "connected to"
            not in output
            and
            "already connected"
            not in output
        ):

            logger.warning(
                f"WiFi verification failed: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

            return False


        #
        # Confirm that the network device appears
        # in `adb devices`.
        #

        for _ in range(5):

            devices = self.get_devices()


            if address in devices:

                logger.info(
                    f"WiFi ADB verified: "
                    f"{address}"
                )

                return True


            time.sleep(
                1
            )


        logger.warning(
            f"WiFi device did not appear in "
            f"ADB device list: {address}"
        )

        return False


    #
    # Connect WiFi fallback
    #

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


        #
        # First check whether the device is already
        # connected through ADB.
        #

        devices = self.get_devices()


        if address in devices:

            self.device = address


            self._update_wifi_device_store()


            logger.info(
                f"Using existing WiFi Pixel: "
                f"{address}"
            )

            return True


        logger.info(
            f"Connecting to WiFi Pixel: "
            f"{address}"
        )


        result = self._run_adb(
            "connect",
            address,
            timeout=15
        )


        if not result:

            return False


        output = (
            result.stdout.lower()
            +
            result.stderr.lower()
        )


        if (
            "connected to" in output
            or
            "already connected" in output
        ):

            #
            # Confirm it actually appears.
            #

            for _ in range(5):

                devices = self.get_devices()


                if address in devices:

                    self.device = address


                    self._update_wifi_device_store()


                    logger.info(
                        f"Using WiFi Pixel: "
                        f"{address}"
                    )

                    return True


                time.sleep(
                    1
                )


        logger.warning(
            f"WiFi Pixel connection failed: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )

        return False


    def _update_wifi_device_store(self):

        stored = self.device_store.find_by_wifi(
            self.config.wifi_address
        )


        if stored:

            serial = stored.get(
                "serial"
            )

        elif self.device_serial:

            serial = self.device_serial

        else:

            serial = self.device


        self.device_serial = serial or ""


        self.device_store.update_device(
            serial=serial,
            wifi_address=self.config.wifi_address,
            transport="wifi"
        )


    #
    # Disconnect WiFi
    #

    def disconnect_wifi(
        self,
        device=None
    ):

        target = device or self.device


        if not target:

            return


        if ":" not in target:

            return


        result = self._run_adb(
            "disconnect",
            target,
            timeout=10
        )


        if result:

            logger.info(
                f"Disconnected WiFi Pixel: "
                f"{target}"
            )


    #
    # Connection status
    #

    def is_connected(self):

        if not self.device:

            return False


        devices = self.get_devices()


        return self.device in devices


    #
    # Model
    #

    def get_model(self):

        if not self.device:

            return None


        result = self._run_adb(
            "-s",
            self.device,
            "shell",
            "getprop",
            "ro.product.model"
        )


        if not result:

            return None


        if result.returncode != 0:

            logger.warning(
                f"Unable to get device model: "
                f"{result.stderr.strip()}"
            )

            return None


        return result.stdout.strip()


    #
    # Transport
    #

    def get_transport(self):

        if not self.device:

            return None


        if ":" in self.device:

            return "wifi"


        return "usb"


    #
    # Learn Pixel WiFi address
    #

    def learn_wifi_address(self):

        if self.get_transport() != "usb":

            return False


        if not self.device:

            return False


        result = self._run_adb(
            "-s",
            self.device,
            "shell",
            "ip",
            "addr",
            "show",
            "wlan0"
        )


        if not result:

            return False


        for line in result.stdout.splitlines():

            if "inet " not in line:

                continue


            try:

                ip = (
                    line.strip()
                    .split()[1]
                    .split("/")[0]
                )

            except Exception:

                continue


            #
            # Ignore loopback and invalid values.
            #

            if (
                not ip
                or
                ip.startswith("127.")
            ):

                continue


            if self.config.wifi_address != ip:

                self.config.set_wifi_address(
                    ip
                )


                logger.info(
                    f"Saved WiFi Pixel address: "
                    f"{ip}"
                )


            self.device_store.update_device(
                serial=self.device,
                wifi_address=ip,
                transport="usb"
            )


            return True


        logger.warning(
            "Unable to determine Pixel WiFi address"
        )

        return False
