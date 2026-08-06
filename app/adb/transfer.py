from pathlib import Path
import subprocess
import time

from loguru import logger


MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


class TransferManager:

    def __init__(self, adb):

        self.adb = adb


    def push_file(self, file_path, destination):

        file_path = Path(file_path)

        attempt = 1

        while attempt <= MAX_RETRIES:

            logger.info(
                f"Sending {file_path.name} "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            try:

                result = subprocess.run(
                    [
                        "adb",
                        "push",
                        str(file_path),
                        destination
                    ],
                    capture_output=True,
                    text=True
                )


                if result.returncode == 0:

                    logger.info(
                        f"Transfer complete: {file_path.name}"
                    )

                    self.scan_media(
                        destination + file_path.name
                    )

                    return True


                logger.error(
                    result.stderr.strip()
                )


            except Exception as error:

                logger.error(
                    f"Transfer exception: {error}"
                )


            if attempt < MAX_RETRIES:

                logger.info(
                    f"Retrying in {RETRY_DELAY_SECONDS} seconds..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )


            attempt += 1


        logger.error(
            f"Transfer failed permanently: {file_path.name}"
        )

        return False



    def scan_media(self, path):

        try:

            subprocess.run(
                [
                    "adb",
                    "shell",
                    "am",
                    "broadcast",
                    "-a",
                    "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                    "-d",
                    f"file://{path}"
                ],
                capture_output=True,
                text=True
            )


            logger.info(
                f"Media scan triggered: {path}"
            )


        except Exception as error:

            logger.error(
                f"Media scan failed: {error}"
            )