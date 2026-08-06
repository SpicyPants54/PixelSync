import threading
import time

from loguru import logger


class DeviceMonitor:

    def __init__(self, adb):

        self.adb = adb
        self.running = False
        self.thread = None

        self.last_connected = False
        self.last_transport = None
        self.last_model = None


    def start(self):

        if self.running:
            return


        self.running = True

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        self.thread.start()


        logger.info(
            "Device monitor started"
        )


    def run(self):

        while self.running:

            try:

                connected = self.adb.is_connected()


                if connected:

                    transport = self.adb.get_transport()
                    model = self.adb.get_model()


                    if not self.last_connected:

                        logger.info(
                            f"Pixel connected: {self.adb.device}"
                        )


                    if transport != self.last_transport:

                        logger.info(
                            f"Transport changed: {transport}"
                        )


                    if model and model != self.last_model:

                        logger.info(
                            f"Device model: {model}"
                        )


                    self.last_connected = True
                    self.last_transport = transport
                    self.last_model = model


                else:

                    if self.last_connected:

                        logger.warning(
                            "Pixel disconnected"
                        )


                    self.last_connected = False

                    self.adb.connect()


            except Exception as error:

                logger.error(
                    f"Device monitor error: {error}"
                )


            time.sleep(10)


    def stop(self):

        self.running = False

        logger.info(
            "Device monitor stopped"
        )