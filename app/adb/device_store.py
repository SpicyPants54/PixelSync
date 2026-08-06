import json
from pathlib import Path
from datetime import datetime

from loguru import logger


class DeviceStore:

    def __init__(self):

        self.file = (
            Path("config")
            /
            "devices.json"
        )

        self.devices = []

        self.load()



    def load(self):

        if not self.file.exists():

            self.devices = []
            return


        try:

            with open(
                self.file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                self.devices = data.get(
                    "devices",
                    []
                )


        except Exception as error:

            logger.error(
                f"Device store load failed: {error}"
            )

            self.devices = []



    def save(self):

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with open(
            self.file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                {
                    "devices": self.devices
                },
                file,
                indent=4
            )



    def find_by_serial(
        self,
        serial
    ):

        for device in self.devices:

            if device.get("serial") == serial:

                return device


        return None



    def find_by_wifi(
        self,
        wifi_address
    ):

        for device in self.devices:

            if device.get("wifi_address") == wifi_address:

                return device


        return None



    def get_wifi_address(
        self,
        serial
    ):

        device = self.find_by_serial(
            serial
        )


        if device:

            return device.get(
                "wifi_address"
            )


        return None



    def update_device(
        self,
        serial,
        name=None,
        wifi_address=None,
        transport=None
    ):

        device = self.find_by_serial(
            serial
        )


        if not device:

            device = {
                "serial": serial
            }

            self.devices.append(
                device
            )



        if name:

            device["name"] = name



        if wifi_address:

            device["wifi_address"] = wifi_address



        if transport:

            device["last_transport"] = transport



        device["last_seen"] = (
            datetime.utcnow()
            .isoformat()
        )


        self.save()


        logger.info(
            f"Device memory updated: {serial}"
        )