from pathlib import Path
import json

from loguru import logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_FILE = PROJECT_ROOT / "config" / "settings.json"


class Settings:

    def __init__(self):
        self.load()


    def load(self):

        if not CONFIG_FILE.exists():

            raise FileNotFoundError(
                f"Missing settings file: {CONFIG_FILE}"
            )


        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            self.data = json.load(file)


        logger.info(
            "Settings loaded"
        )


    @property
    def import_folder(self):

        folder = (
            Path.home()
            /
            self.data["import_folder"]
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return str(folder)


    @property
    def pixel_folder(self):

        return self.data[
            "pixel_destination"
        ]


    @property
    def database_file(self):

        database_path = Path(
            self.data["database"]
        )

        if not database_path.is_absolute():

            database_path = PROJECT_ROOT / database_path


        database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        return str(database_path)


    @property
    def log_folder(self):

        folder = (
            PROJECT_ROOT
            /
            self.data.get(
                "log_folder",
                "logs"
            )
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return str(folder)


    @property
    def retry_count(self):

        return self.data["transfer"]["retry_count"]


    @property
    def retry_delay(self):

        return self.data["transfer"]["retry_delay_seconds"]


    @property
    def prefer_usb(self):

        return self.data.get(
            "connection",
            {}
        ).get(
            "prefer_usb",
            True
        )


    @property
    def wifi_fallback(self):

        return self.data.get(
            "connection",
            {}
        ).get(
            "wifi_fallback",
            False
        )


    @property
    def wifi_port(self):

        return self.data.get(
            "connection",
            {}
        ).get(
            "wifi_port",
            5555
        )


    @property
    def wifi_address(self):

        return self.data.get(
            "connection",
            {}
        ).get(
            "wifi_address",
            None
        )


    def save_wifi_address(self, address):

        connection = self.data.setdefault(
            "connection",
            {}
        )

        connection["wifi_address"] = address


        with open(
            CONFIG_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4
            )