from sqlalchemy import inspect, text

from loguru import logger


def migrate_database(engine):

    logger.info(
        "Checking database schema..."
    )

    inspector = inspect(
        engine
    )

    tables = inspector.get_table_names()

    migration_applied = False


    #
    # Transfers table migrations
    #

    if "transfers" in tables:

        transfer_columns = {
            column["name"]
            for column in inspector.get_columns(
                "transfers"
            )
        }

        transfer_migrations = {

            "attempts": (
                "ALTER TABLE transfers "
                "ADD COLUMN attempts INTEGER DEFAULT 0"
            ),

            "error": (
                "ALTER TABLE transfers "
                "ADD COLUMN error VARCHAR"
            ),

            "started_at": (
                "ALTER TABLE transfers "
                "ADD COLUMN started_at DATETIME"
            ),

            "completed_at": (
                "ALTER TABLE transfers "
                "ADD COLUMN completed_at DATETIME"
            ),

        }

        with engine.begin() as connection:

            for name, statement in (
                transfer_migrations.items()
            ):

                if name in transfer_columns:

                    logger.debug(
                        f"Database column already exists: "
                        f"transfers.{name}"
                    )

                    continue

                logger.info(
                    f"Adding database column: "
                    f"transfers.{name}"
                )

                connection.execute(
                    text(statement)
                )

                migration_applied = True

    else:

        logger.info(
            "Transfers table does not exist; "
            "SQLAlchemy will create it."
        )


    #
    # Transfer jobs table migrations
    #

    if "transfer_jobs" in tables:

        job_columns = {
            column["name"]
            for column in inspector.get_columns(
                "transfer_jobs"
            )
        }

        job_migrations = {

            "error": (
                "ALTER TABLE transfer_jobs "
                "ADD COLUMN error VARCHAR"
            ),

            "started_at": (
                "ALTER TABLE transfer_jobs "
                "ADD COLUMN started_at DATETIME"
            ),

            "completed_at": (
                "ALTER TABLE transfer_jobs "
                "ADD COLUMN completed_at DATETIME"
            ),

        }

        with engine.begin() as connection:

            for name, statement in (
                job_migrations.items()
            ):

                if name in job_columns:

                    logger.debug(
                        f"Database column already exists: "
                        f"transfer_jobs.{name}"
                    )

                    continue

                logger.info(
                    f"Adding database column: "
                    f"transfer_jobs.{name}"
                )

                connection.execute(
                    text(statement)
                )

                migration_applied = True

    else:

        logger.info(
            "Transfer jobs table does not exist; "
            "SQLAlchemy will create it."
        )


    #
    # Migration result
    #

    if migration_applied:

        logger.info(
            "Database schema upgraded successfully"
        )

    else:

        logger.info(
            "Database schema is already current"
        )