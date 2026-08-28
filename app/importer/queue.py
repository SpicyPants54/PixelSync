from datetime import datetime
from pathlib import Path
from threading import RLock

from loguru import logger

from app.core.models import TransferJob


class TransferQueue:

    MAX_ATTEMPTS = 3

    def __init__(
        self,
        session=None
    ):
        self.session = session

        self.lock = RLock()

        logger.info(
            "Transfer queue initialized"
        )

        self.recover_interrupted_jobs()


    #
    # Startup recovery
    #

    def recover_interrupted_jobs(self):

        if not self.session:

            logger.warning(
                "Transfer queue has no database session"
            )

            return

        with self.lock:

            try:

                interrupted_jobs = (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.status
                        == "processing"
                    )
                    .all()
                )

                recovered_count = 0

                for job in interrupted_jobs:

                    job.status = "pending"

                    job.error = (
                        "Recovered after application "
                        "restart"
                    )

                    job.started_at = None

                    job.updated_at = (
                        datetime.utcnow()
                    )

                    recovered_count += 1

                self.session.commit()

                if recovered_count:

                    logger.warning(
                        f"Recovered {recovered_count} "
                        f"interrupted transfer job(s)"
                    )

                else:

                    logger.info(
                        "No interrupted transfer jobs "
                        "to recover"
                    )

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to recover interrupted "
                    f"transfer jobs: {error}"
                )


    #
    # Add job
    #

    def add(
        self,
        file
    ):

        file = Path(file)

        if not file.exists():

            logger.warning(
                f"Cannot queue missing file: "
                f"{file}"
            )

            return False

        if not self.session:

            logger.error(
                "Cannot queue file without "
                "database session"
            )

            return False

        with self.lock:

            try:

                filepath = str(
                    file.resolve()
                )

                existing_job = (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.filepath
                        == filepath
                    )
                    .first()
                )

                if existing_job:

                    if (
                        existing_job.status
                        == "completed"
                    ):

                        logger.debug(
                            f"File already completed: "
                            f"{file.name}"
                        )

                        return False

                    if (
                        existing_job.status
                        == "processing"
                    ):

                        logger.debug(
                            f"File already processing: "
                            f"{file.name}"
                        )

                        return False

                    if (
                        existing_job.status
                        == "failed"
                    ):

                        existing_job.attempts = 0

                        existing_job.completed_at = None

                    existing_job.status = "pending"

                    existing_job.error = None

                    existing_job.started_at = None

                    existing_job.updated_at = (
                        datetime.utcnow()
                    )

                    self.session.commit()

                    logger.info(
                        f"Re-queued transfer job: "
                        f"{file.name}"
                    )

                    return True


                job = TransferJob(
                    filepath=filepath,
                    filename=file.name,
                    status="pending",
                    attempts=0,
                    error=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                self.session.add(
                    job
                )

                self.session.commit()

                logger.info(
                    f"Added to persistent "
                    f"transfer queue: "
                    f"{file.name}"
                )

                return True

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to add transfer job "
                    f"{file.name}: {error}"
                )

                return False


    #
    # Get next pending job
    #

    def get_next(self):

        if not self.session:

            return None

        with self.lock:

            try:

                while True:

                    job = (
                        self.session.query(
                            TransferJob
                        )
                        .filter(
                            TransferJob.status
                            == "pending"
                        )
                        .filter(
                            TransferJob.attempts
                            < self.MAX_ATTEMPTS
                        )
                        .order_by(
                            TransferJob.created_at.asc()
                        )
                        .first()
                    )

                    if not job:

                        return None


                    file = Path(
                        job.filepath
                    )


                    #
                    # Source file disappeared.
                    #
                    # Mark it failed and continue
                    # looking for another job.
                    #

                    if not file.exists():

                        job.status = "failed"

                        job.error = (
                            "Source file no longer exists"
                        )

                        job.completed_at = (
                            datetime.utcnow()
                        )

                        job.updated_at = (
                            datetime.utcnow()
                        )

                        self.session.commit()

                        logger.error(
                            f"Queued file disappeared: "
                            f"{job.filename}"
                        )

                        continue


                    #
                    # Mark job as actively processing.
                    #

                    job.status = "processing"

                    job.attempts = (
                        (job.attempts or 0)
                        + 1
                    )

                    job.started_at = (
                        datetime.utcnow()
                    )

                    job.completed_at = None

                    job.error = None

                    job.updated_at = (
                        datetime.utcnow()
                    )

                    self.session.commit()

                    logger.info(
                        f"Dequeued transfer job: "
                        f"{job.filename} "
                        f"(attempt {job.attempts}/"
                        f"{self.MAX_ATTEMPTS})"
                    )

                    return file

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to get next "
                    f"transfer job: {error}"
                )

                return None


    #
    # Mark job completed
    #

    def complete(
        self,
        file
    ):

        file = Path(file)

        if not self.session:

            return False

        with self.lock:

            try:

                filepath = str(
                    file.resolve()
                )

                job = (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.filepath
                        == filepath
                    )
                    .first()
                )

                if not job:

                    logger.warning(
                        f"No queue job found for "
                        f"completed file: "
                        f"{file.name}"
                    )

                    return False


                job.status = "completed"

                job.error = None

                job.completed_at = (
                    datetime.utcnow()
                )

                job.updated_at = (
                    datetime.utcnow()
                )

                self.session.commit()

                logger.info(
                    f"Transfer queue job completed: "
                    f"{file.name}"
                )

                return True

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to complete queue job "
                    f"{file.name}: {error}"
                )

                return False


    #
    # Mark job failed or return it
    # to the queue for retry.
    #

    def fail(
        self,
        file,
        error=""
    ):

        file = Path(file)

        if not self.session:

            return False

        with self.lock:

            try:

                filepath = str(
                    file.resolve()
                )

                job = (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.filepath
                        == filepath
                    )
                    .first()
                )

                if not job:

                    logger.warning(
                        f"No queue job found for "
                        f"failed file: "
                        f"{file.name}"
                    )

                    return False


                job.error = (
                    error
                    or
                    "Transfer failed"
                )

                job.updated_at = (
                    datetime.utcnow()
                )


                #
                # Retry if attempts remain.
                #

                if (
                    (job.attempts or 0)
                    < self.MAX_ATTEMPTS
                ):

                    job.status = "pending"

                    job.started_at = None

                    job.completed_at = None

                    logger.warning(
                        f"Transfer failed, "
                        f"returning to queue: "
                        f"{file.name} "
                        f"(attempt {job.attempts}/"
                        f"{self.MAX_ATTEMPTS})"
                    )

                else:

                    job.status = "failed"

                    job.completed_at = (
                        datetime.utcnow()
                    )

                    logger.error(
                        f"Transfer permanently failed: "
                        f"{file.name} "
                        f"after {job.attempts} "
                        f"attempt(s)"
                    )


                self.session.commit()

                return True

            except Exception as exception:

                self.session.rollback()

                logger.exception(
                    f"Failed to update queue job "
                    f"{file.name}: {exception}"
                )

                return False


    #
    # Queue status helpers
    #

    def count_pending(self):

        if not self.session:

            return 0

        with self.lock:

            try:

                return (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.status
                        == "pending"
                    )
                    .count()
                )

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to count pending "
                    f"transfer jobs: {error}"
                )

                return 0


    def count_processing(self):

        if not self.session:

            return 0

        with self.lock:

            try:

                return (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.status
                        == "processing"
                    )
                    .count()
                )

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to count processing "
                    f"transfer jobs: {error}"
                )

                return 0


    def count_failed(self):

        if not self.session:

            return 0

        with self.lock:

            try:

                return (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.status
                        == "failed"
                    )
                    .count()
                )

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to count failed "
                    f"transfer jobs: {error}"
                )

                return 0


    def count_completed(self):

        if not self.session:

            return 0

        with self.lock:

            try:

                return (
                    self.session.query(
                        TransferJob
                    )
                    .filter(
                        TransferJob.status
                        == "completed"
                    )
                    .count()
                )

            except Exception as error:

                self.session.rollback()

                logger.exception(
                    f"Failed to count completed "
                    f"transfer jobs: {error}"
                )

                return 0


    def count_total_active(self):

        return (
            self.count_pending()
            +
            self.count_processing()
        )