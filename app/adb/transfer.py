from pathlib import Path
import subprocess
from loguru import logger


class TransferManager:

    def __init__(self, device):

        self.device = device


    def push_file(self, source, destination_folder):

        source = Path(source)

        if not source.exists():

            logger.error(
                f"File not found: {source}"
            )

            return False


        destination = (
            destination_folder.rstrip("/")
            + "/"
            + source.name
        )


        logger.info(
            f"Sending {source.name}"
        )


        result = subprocess.run(
            [
                "adb",
                "-s",
                self.device,
                "push",
                str(source),
                destination
            ],
            capture_output=True,
            text=True
        )


        if result.returncode == 0:

            logger.info(
                f"Transfer complete: {source.name}"
            )

            self.scan_media(
                destination
            )

            return True


        logger.error(
            result.stderr
        )

        return False


    def scan_media(self, file_path):

        result = subprocess.run(
            [
                "adb",
                "-s",
                self.device,
                "shell",
                "am",
                "broadcast",
                "-a",
                "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                "-d",
                f"file://{file_path}"
            ],
            capture_output=True,
            text=True
        )


        if result.returncode == 0:

            logger.info(
                f"Media scan triggered: {file_path}"
            )

            return True


        logger.error(
            result.stderr
        )

        return False