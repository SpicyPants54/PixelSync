from pathlib import Path, PurePosixPath

from loguru import logger

from app.importer.iphone_afc import IPhoneAFC


class IPhoneImporter:

    def __init__(
        self,
        connector,
        import_folder,
        afc_factory=IPhoneAFC
    ):

        self.connector = connector
        self.import_folder = Path(
            import_folder
        )
        self.afc_factory = afc_factory


    def get_destination(
        self,
        remote_path,
        remote_size
    ):

        remote_path = PurePosixPath(
            remote_path
        )

        relative_path = remote_path.relative_to(
            "/DCIM"
        )

        destination = (
            self.import_folder
            /
            "iPhone"
            /
            self.connector.udid
            /
            Path(*relative_path.parts)
        )

        if (
            destination.is_file()
            and
            destination.stat().st_size
            != remote_size
        ):

            destination = destination.with_name(
                f"{destination.stem}-"
                f"{remote_size}"
                f"{destination.suffix}"
            )

        return destination


    def sync(
        self,
        max_files=None
    ):

        summary = {
            "discovered": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
        }

        if not self.connector.connect():

            logger.info(
                "No iPhone is available for import"
            )

            return summary

        afc = self.afc_factory(
            self.connector.tool_directory,
            self.connector.udid,
            self.connector.transport
        )

        with afc:

            for remote_path, info in afc.walk_media():

                summary["discovered"] += 1

                try:

                    remote_size = int(
                        info.get(
                            "st_size",
                            0
                        )
                    )

                    destination = self.get_destination(
                        remote_path,
                        remote_size
                    )

                    if (
                        destination.is_file()
                        and
                        destination.stat().st_size
                        == remote_size
                    ):

                        summary["skipped"] += 1

                        continue

                    afc.download(
                        remote_path,
                        destination
                    )

                    if (
                        remote_size
                        and
                        destination.stat().st_size
                        != remote_size
                    ):

                        destination.unlink(
                            missing_ok=True
                        )

                        raise IOError(
                            "Downloaded file size does "
                            "not match the iPhone file"
                        )

                    summary["downloaded"] += 1

                except Exception as error:

                    summary["failed"] += 1

                    logger.warning(
                        f"Unable to import "
                        f"{remote_path}: {error}"
                    )

                if (
                    max_files is not None
                    and
                    summary["downloaded"]
                    >= max_files
                ):

                    break

        return summary
