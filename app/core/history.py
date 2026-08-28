from datetime import datetime

from loguru import logger

from app.core.models import Transfer


class TransferHistory:

    def __init__(
        self,
        session
    ):
        self.session = session


    #
    # Duplicate detection
    #

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

            self.session.rollback()

            logger.exception(
                f"Transfer history lookup failed: "
                f"{error}"
            )

            return False


    #
    # Start or retry transfer
    #

    def start(
        self,
        filename,
        file_hash,
        size,
        device="",
        transport=""
    ):
        logger.info(
            f"Starting transfer history: "
            f"{filename}"
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

            now = datetime.utcnow()

            if transfer:

                previous_attempts = (
                    transfer.attempts or 0
                )

                transfer.filename = filename

                transfer.file_size = size

                transfer.status = "transferring"

                transfer.attempts = (
                    previous_attempts + 1
                )

                transfer.device = device

                transfer.transport = transport

                transfer.error = None

                transfer.duration = None

                transfer.started_at = now

                transfer.completed_at = None

                transfer.transferred_at = None

                logger.info(
                    f"Retrying transfer: "
                    f"{filename} "
                    f"(attempt {transfer.attempts})"
                )

            else:

                transfer = Transfer(
                    filename=filename,
                    file_hash=file_hash,
                    file_size=size,
                    status="transferring",
                    attempts=1,
                    device=device,
                    transport=transport,
                    error=None,
                    duration=None,
                    started_at=now,
                    completed_at=None,
                    transferred_at=None
                )

                self.session.add(
                    transfer
                )

                logger.info(
                    f"Created transfer history: "
                    f"{filename} "
                    f"(attempt 1)"
                )

            self.session.commit()

            return True

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Failed to start transfer history "
                f"for {filename}: {error}"
            )

            return False


    #
    # Mark transfer successful
    #

    def add(
        self,
        filename,
        file_hash,
        size,
        device="",
        transport="",
        duration=0
    ):
        logger.info(
            f"Recording successful transfer: "
            f"{filename}"
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

            now = datetime.utcnow()

            if transfer:

                transfer.filename = filename

                transfer.file_size = size

                transfer.status = "success"

                transfer.device = device

                transfer.transport = transport

                transfer.duration = float(
                    duration or 0
                )

                transfer.error = None

                transfer.completed_at = now

                transfer.transferred_at = now

                if not transfer.started_at:

                    transfer.started_at = now

                logger.info(
                    f"Finalizing existing transfer: "
                    f"{filename} "
                    f"(attempt {transfer.attempts})"
                )

            else:

                logger.warning(
                    f"No active transfer history found "
                    f"for {filename}. "
                    f"Creating completed record."
                )

                transfer = Transfer(
                    filename=filename,
                    file_hash=file_hash,
                    file_size=size,
                    status="success",
                    attempts=1,
                    device=device,
                    transport=transport,
                    duration=float(
                        duration or 0
                    ),
                    error=None,
                    started_at=now,
                    completed_at=now,
                    transferred_at=now
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


    #
    # Mark transfer failed
    #

    def mark_failed(
        self,
        file_hash,
        error=""
    ):
        logger.warning(
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

            if not transfer:

                logger.warning(
                    f"No transfer history found "
                    f"to mark failed: {file_hash}"
                )

                return False

            now = datetime.utcnow()

            transfer.status = "failed"

            transfer.error = (
                str(error)
                if error
                else "Transfer failed"
            )

            transfer.completed_at = now

            self.session.commit()

            logger.warning(
                f"Transfer marked failed: "
                f"{transfer.filename} "
                f"(attempt {transfer.attempts})"
            )

            return True

        except Exception as exception:

            self.session.rollback()

            logger.exception(
                f"Failed to mark transfer failed: "
                f"{file_hash}: {exception}"
            )

            return False


    #
    # Retrieve transfer
    #

    def get(
        self,
        file_hash
    ):
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

            return transfer

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Transfer history lookup failed: "
                f"{file_hash}: {error}"
            )

            return None


    #
    # Retrieve incomplete transfers
    #

    def get_incomplete(
        self
    ):
        try:

            transfers = (
                self.session.query(
                    Transfer
                )
                .filter(
                    Transfer.status.in_(
                        [
                            "transferring",
                            "failed"
                        ]
                    )
                )
                .order_by(
                    Transfer.started_at.asc()
                )
                .all()
            )

            return transfers

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Failed to retrieve incomplete "
                f"transfers: {error}"
            )

            return []


    #
    # Remove transfer history
    #

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

            filename = transfer.filename

            self.session.delete(
                transfer
            )

            self.session.commit()

            logger.info(
                f"Transfer history removed: "
                f"{filename}"
            )

            return True

        except Exception as error:

            self.session.rollback()

            logger.exception(
                f"Failed to remove transfer history: "
                f"{file_hash}: {error}"
            )

            return False