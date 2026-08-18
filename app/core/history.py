from loguru import logger

from app.core.models import Transfer


class TransferHistory:

    def __init__(
        self,
        session
    ):
        self.session = session

    def exists(
        self,
        file_hash
    ):
        logger.debug(
            f"Checking transfer history: {file_hash}"
        )

        try:

            transfer = (
                self.session.query(
                    Transfer
                )
                .filter(
                    Transfer.file_hash == file_hash,
                    Transfer.status == "success"
                )
                .first()
            )

            exists = transfer is not None

            logger.debug(
                f"Transfer history result: "
                f"{file_hash} -> {exists}"
            )

            return exists

        except Exception as error:

            logger.exception(
                f"Transfer history lookup failed: "
                f"{error}"
            )

            return False

    def add(
        self,
        filename,
        file_hash,
        size,
        device,
        transport,
        duration
    ):
        logger.info(
            f"Recording transfer history: "
            f"{filename}"
        )

        try:

            existing = (
                self.session.query(
                    Transfer
                )
                .filter(
                    Transfer.file_hash == file_hash
                )
                .first()
            )

            if existing:

                existing.filename = filename
                existing.file_size = size
                existing.status = "success"
                existing.device = device
                existing.transport = transport
                existing.duration = duration

                self.session.commit()

                logger.info(
                    f"Transfer history updated: "
                    f"{filename}"
                )

                return True

            transfer = Transfer(
                filename=filename,
                file_hash=file_hash,
                file_size=size,
                status="success",
                device=device,
                transport=transport,
                duration=duration
            )

            self.session.add(
                transfer
            )

            self.session.commit()

            logger.info(
                f"Transfer history recorded: "
                f"{filename}"
            )

            return True

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Failed to record transfer history "
                f"for {filename}: {error}"
            )

            return False

    def mark_failed(
        self,
        file_hash
    ):
        logger.info(
            f"Marking transfer failed: "
            f"{file_hash}"
        )

        try:

            transfer = (
                self.session.query(
                    Transfer
                )
                .filter(
                    Transfer.file_hash == file_hash
                )
                .first()
            )

            if transfer:

                transfer.status = "failed"

                self.session.commit()

                logger.info(
                    f"Transfer marked failed: "
                    f"{file_hash}"
                )

                return True

            return False

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Failed to mark transfer failed: "
                f"{file_hash}: {error}"
            )

            return False

    def remove(
        self,
        file_hash
    ):
        logger.info(
            f"Removing transfer history: "
            f"{file_hash}"
        )

        try:

            transfer = (
                self.session.query(
                    Transfer
                )
                .filter(
                    Transfer.file_hash == file_hash
                )
                .first()
            )

            if not transfer:

                logger.debug(
                    f"No history entry found: "
                    f"{file_hash}"
                )

                return False

            self.session.delete(
                transfer
            )

            self.session.commit()

            logger.info(
                f"Transfer history removed: "
                f"{file_hash}"
            )

            return True

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Failed to remove transfer history: "
                f"{file_hash}: {error}"
            )

            return False