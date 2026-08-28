import threading
import time

from loguru import logger


class DeviceMonitor:

    def __init__(
        self,
        adb,
        callback=None,
        transfer=None
    ):

        self.adb = adb
        self.callback = callback
        self.transfer = transfer

        self.running = False
        self.thread = None

        self.last_transport = None
        self.was_connected = False


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

                #
                # Always check USB first
                #

                usb_device = self.adb.get_usb_device()


                if usb_device:

                    if self.adb.device != usb_device:

                        if (
                            self.transfer
                            and
                            self.transfer.active_transfer
                        ):

                            logger.info(
                                "USB device detected, "
                                "deferring transport switch "
                                "until active transfer finishes"
                            )

                            self.report_device()

                            time.sleep(10)

                            continue

                        logger.info(
                            f"USB device detected, "
                            f"switching from "
                            f"{self.adb.device} "
                            f"to {usb_device}"
                        )


                        self.adb.use_usb_device(
                            usb_device
                        )


                    self.report_device()

                    time.sleep(10)

                    continue


                #
                # No USB device.
                #
                # Keep the current connection
                # if it is still alive.
                #

                if self.adb.is_connected():

                    self.report_device()


                else:

                    if self.was_connected:

                        logger.warning(
                            "Pixel disconnected"
                        )


                        self.was_connected = False


                        self.notify_callback(
                            connected=False
                        )


                    self.adb.connect()


                    #
                    # If reconnect succeeds,
                    # report the device immediately.
                    #

                    if self.adb.is_connected():

                        self.report_device()


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


        serial = self.adb.device


        logger.info(
            f"Pixel connected: {serial}"
        )


        model = self.adb.get_model()


        if model:

            logger.info(
                f"Device model: {model}"
            )


        self.was_connected = True


        self.notify_callback(
            connected=True,
            serial=serial or "",
            model=model or "",
            transport=transport or ""
        )


    def notify_callback(
        self,
        connected,
        serial="",
        model="",
        transport=""
    ):

        if not self.callback:

            return


        try:

            self.callback(
                connected=connected,
                serial=serial,
                model=model,
                transport=transport
            )


        except Exception as error:

            logger.exception(
                f"Device monitor callback failed: {error}"
            )


    def stop(self):

        if not self.running:
            return


        logger.info(
            "Stopping device monitor"
        )


        self.running = False


        if (
            self.thread
            and
            self.thread.is_alive()
        ):

            self.thread.join(
                timeout=5
            )


        self.thread = None


        logger.info(
            "Device monitor stopped"
        )
