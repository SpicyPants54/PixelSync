from pathlib import Path
import subprocess
import time

from loguru import logger


class TransferManager:

    def __init__(self, adb, config):

        self.adb = adb
        self.config = config



    def push_file(self, file_path):

        file_path = Path(file_path)

        destination = self.config.pixel_folder

        attempt = 1


        while attempt <= self.config.retry_count:

            device = self.adb.device


            if not device:

                logger.warning(
                    "No Pixel connected. Transfer paused."
                )

                time.sleep(
                    self.config.retry_delay
                )

                attempt += 1
                continue



            logger.info(
                f"Sending {file_path.name} "
                f"via {device} "
                f"(attempt {attempt}/{self.config.retry_count})"
            )



            try:

                result = subprocess.run(
                    [
                        "adb",
                        "-s",
                        device,
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
                        device,
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



            if attempt < self.config.retry_count:

                logger.info(
                    f"Retrying in {self.config.retry_delay} seconds..."
                )


                time.sleep(
                    self.config.retry_delay
                )



            attempt += 1



        logger.error(
            f"Transfer failed permanently: {file_path.name}"
        )


        return False




    def scan_media(self, device, path):

        try:

            subprocess.run(
                [
                    "adb",
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
                text=True
            )


            logger.info(
                f"Media scan triggered: {path}"
            )



        except Exception as error:

            logger.error(
                f"Media scan failed: {error}"
            )