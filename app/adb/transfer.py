from pathlib import Path
import subprocess
import time

from loguru import logger

from app.core.events import TransferEvents


class TransferManager:

    def __init__(
        self,
        adb,
        config,
        events=None
    ):
        self.adb = adb
        self.config = config
        self.events = events or TransferEvents()

        # Used by device monitor to avoid reacting
        # to transport changes during active transfers
        self.active_transfer = False

    def wait_for_device_ready(
        self,
        device,
        timeout=10
    ):
        logger.info(
            f"Checking ADB readiness: {device}"
        )

        start = time.time()

        while time.time() - start < timeout:

            try:

                result = subprocess.run(
                    [
                        self.adb.adb_path,
                        "-s",
                        device,
                        "get-state"
                    ],
                    capture_output=True,
                    text=True
                )

            except Exception as error:

                logger.error(
                    f"ADB readiness check failed: "
                    f"{error}"
                )

                return False

            if result.stdout.strip() == "device":

                logger.info(
                    f"ADB device ready: {device}"
                )

                return True

            time.sleep(1)

        logger.warning(
            f"ADB device not ready: {device}"
        )

        return False

    def refresh_connection(self):

        old = self.adb.device

        logger.warning(
            f"Refreshing Pixel connection "
            f"(old={old})"
        )

        if self.adb.connect():

            logger.info(
                f"Connection restored: "
                f"{self.adb.device}"
            )

            return True

        logger.error(
            "Unable to restore Pixel connection"
        )

        return False

    def push_file(
        self,
        file_path,
        destination=None
    ):
        file_path = Path(file_path)

        if destination is None:
            destination = self.config.pixel_folder

        total_size = file_path.stat().st_size

        attempt = 1

        self.events.started(
            filename=file_path.name,
            size=total_size
        )

        while attempt <= self.config.retry_count:

            device = self.adb.device

            if not device:

                logger.warning(
                    "No Pixel connected. "
                    "Transfer paused."
                )

                time.sleep(
                    self.config.retry_delay
                )

                attempt += 1
                continue

            if not self.wait_for_device_ready(
                device
            ):

                self.refresh_connection()

                attempt += 1
                continue

            logger.info(
                f"Sending {file_path.name} "
                f"via {device} "
                f"(attempt "
                f"{attempt}/"
                f"{self.config.retry_count})"
            )

            start_time = time.time()

            self.active_transfer = True

            process = None

            try:

                process = subprocess.Popen(
                    [
                        self.adb.adb_path,
                        "-s",
                        device,
                        "push",
                        str(file_path),
                        destination
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                last_percent = -1

                while process.poll() is None:

                    elapsed = (
                        time.time()
                        -
                        start_time
                    )

                    if elapsed > 0:

                        # ADB push does not provide
                        # reliable machine-readable
                        # progress, so this is an
                        # estimated progress display.

                        transferred = min(
                            total_size,
                            int(
                                total_size
                                *
                                min(
                                    elapsed / 5,
                                    1
                                )
                            )
                        )

                        percent = int(
                            transferred
                            /
                            total_size
                            *
                            100
                        )

                        speed = (
                            transferred
                            /
                            elapsed
                            /
                            1024
                            /
                            1024
                        )

                        remaining = max(
                            total_size
                            -
                            transferred,
                            0
                        )

                        eta = (
                            remaining
                            /
                            (
                                speed
                                *
                                1024
                                *
                                1024
                            )
                            if speed > 0
                            else 0
                        )

                        if percent != last_percent:

                            self.events.progress(
                                filename=file_path.name,
                                transferred=transferred,
                                percent=percent,
                                speed=speed,
                                eta=eta
                            )

                            last_percent = percent

                    time.sleep(0.25)

                stdout, stderr = (
                    process.communicate(
                        timeout=30
                    )
                )

                if process.returncode == 0:

                    elapsed = max(
                        time.time()
                        -
                        start_time,
                        0.01
                    )

                    speed = (
                        total_size
                        /
                        elapsed
                        /
                        1024
                        /
                        1024
                    )

                    self.events.progress(
                        filename=file_path.name,
                        transferred=total_size,
                        percent=100,
                        speed=speed,
                        eta=0
                    )

                    logger.info(
                        f"Transfer complete: "
                        f"{file_path.name}"
                    )

                    remote_path = (
                        destination.rstrip("/")
                        +
                        "/"
                        +
                        file_path.name
                    )

                    self.scan_media(
                        device,
                        remote_path
                    )

                    self.events.finished(
                        filename=file_path.name,
                        device=device
                    )

                    return True

                error = stderr.strip()

                if not error:
                    error = (
                        stdout.strip()
                        or
                        "Unknown ADB error"
                    )

                logger.error(
                    f"ADB transfer failed: "
                    f"{error}"
                )

                if (
                    "device" in error.lower()
                    or
                    "offline" in error.lower()
                    or
                    "transport" in error.lower()
                ):

                    self.refresh_connection()

            except subprocess.TimeoutExpired:

                logger.warning(
                    "ADB process cleanup timeout"
                )

                if process is not None:

                    process.kill()

                    try:

                        process.communicate(
                            timeout=5
                        )

                    except Exception:
                        pass

            except Exception as error:

                logger.exception(
                    f"Transfer exception: "
                    f"{error}"
                )

            finally:

                self.active_transfer = False

            if attempt < self.config.retry_count:

                logger.info(
                    f"Retrying in "
                    f"{self.config.retry_delay} "
                    f"seconds..."
                )

                time.sleep(
                    self.config.retry_delay
                )

            attempt += 1

        self.active_transfer = False

        logger.error(
            f"Transfer failed permanently: "
            f"{file_path.name}"
        )

        self.events.failed(
            filename=file_path.name,
            error="Transfer failed"
        )

        return False

    def scan_media(
        self,
        device,
        path
    ):
        try:

            subprocess.run(
                [
                    self.adb.adb_path,
                    "-s",
                    device,
                    "shell",
                    "am",
                    "broadcast",
                    "-a",
                    "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                    "-d",
                    f"file://{path}"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            logger.info(
                f"Media scan triggered: "
                f"{path}"
            )

        except Exception as error:

            logger.error(
                f"Media scan failed: "
                f"{error}"
            )