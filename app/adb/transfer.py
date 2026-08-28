from collections import deque
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

        # Used by DeviceMonitor to avoid reacting
        # to transport changes during an active transfer.
        self.active_transfer = False

        # Progress polling interval.
        self.progress_interval = 0.5

        # Log a warning if the remote file stops growing
        # for this many seconds.
        self.stall_warning_seconds = 30

        # Number of samples used to smooth transfer speed.
        self.speed_sample_count = 8


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
                    text=True,
                    timeout=10
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


    def get_remote_file_size(
        self,
        device,
        remote_path
    ):
        """
        Return the current size of the destination file.

        ADB on the tested Pixel device writes directly to
        the final destination path, allowing us to monitor
        the file size while the transfer is in progress.

        Returns None if the file does not exist or the size
        cannot be determined.
        """

        try:

            result = subprocess.run(
                [
                    self.adb.adb_path,
                    "-s",
                    device,
                    "shell",
                    "stat",
                    "-c",
                    "%s",
                    remote_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:

                return None

            output = result.stdout.strip()

            if not output:

                return None

            return int(output)

        except (
            ValueError,
            subprocess.TimeoutExpired
        ):

            return None

        except Exception as error:

            logger.debug(
                f"Unable to read remote file size "
                f"for {remote_path}: {error}"
            )

            return None


    def calculate_progress_speed(
        self,
        samples
    ):
        """
        Calculate a smoothed transfer speed in MB/s using
        the oldest and newest progress samples.
        """

        if len(samples) < 2:

            return 0

        oldest_time, oldest_bytes = samples[0]

        newest_time, newest_bytes = samples[-1]

        time_delta = (
            newest_time
            -
            oldest_time
        )

        bytes_delta = (
            newest_bytes
            -
            oldest_bytes
        )

        if (
            time_delta <= 0
            or bytes_delta <= 0
        ):

            return 0

        return (
            bytes_delta
            /
            time_delta
            /
            1024
            /
            1024
        )


    def is_transport_error(
        self,
        error
    ):
        """
        Return True if an ADB error appears to indicate that
        the device connection or transport was lost.
        """

        error = error.lower()

        indicators = [
            "device offline",
            "device not found",
            "device unauthorized",
            "transport",
            "connection reset",
            "connection refused",
            "no devices",
            "closed"
        ]

        return any(
            indicator in error
            for indicator in indicators
        )


    def push_file(
        self,
        file_path,
        destination=None
    ):
        file_path = Path(file_path)

        if destination is None:

            destination = (
                self.config.pixel_folder
            )

        total_size = (
            file_path.stat().st_size
        )

        remote_path = (
            destination.rstrip("/")
            +
            "/"
            +
            file_path.name
        )

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

                while process.poll() is None:

                    #
                    # Do not issue a second ADB command while
                    # `adb push` owns the transport. On the target
                    # Pixel this caused remote `stat` polling to
                    # block and left ADB worker processes hung.
                    #
                    # This ADB version does not offer a supported
                    # live-progress mode for `push`, so completion
                    # telemetry below is the reliable signal.
                    #

                    time.sleep(
                        self.progress_interval
                    )

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
                        f"{file_path.name} "
                        f"in {elapsed:.2f}s "
                        f"({speed:.2f} MB/s)"
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

                if self.is_transport_error(
                    error
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
                    (
                        "android.intent.action."
                        "MEDIA_SCANNER_SCAN_FILE"
                    ),
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
