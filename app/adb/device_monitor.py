import threading
import time

from loguru import logger


class DeviceMonitor:

    def __init__(self, adb):

        self.adb = adb
        self.running = False
        self.thread = None
        self.last_transport = None



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

                # Always check USB first
                usb_device = self.adb.get_usb_device()


                if usb_device:

                    if self.adb.device != usb_device:

                        logger.info(
                            f"USB device detected, switching from {self.adb.device} to {usb_device}"
                        )


                        self.adb.disconnect_wifi()


                        self.adb.device = usb_device


                    self.report_device()

                    time.sleep(10)
                    continue



                # No USB, keep current connection if alive
                if self.adb.is_connected():

                    self.report_device()

                else:

                    logger.warning(
                        "Pixel disconnected"
                    )


                    self.adb.connect()



            except Exception as error:

                logger.error(
                    f"Device monitor error: {error}"
                )


            time.sleep(10)



    def report_device(self):

        transport = self.adb.get_transport()


        if transport != self.last_transport:

            logger.info(
                f"Transport changed: {transport}"
            )

            self.last_transport = transport



        logger.info(
            f"Pixel connected: {self.adb.device}"
        )


        model = self.adb.get_model()


        if model:

            logger.info(
                f"Device model: {model}"
            )