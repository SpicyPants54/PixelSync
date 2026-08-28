import sqlite3
import threading

from sqlalchemy import inspect

from app.core import models  # noqa: F401
from app.core.database import create_database
from app.core.models import TransferJob
from app.importer.queue import TransferQueue


def test_migrates_legacy_transfer_tables(tmp_path):

    database_path = tmp_path / "legacy.db"

    connection = sqlite3.connect(database_path)

    connection.execute(
        """
        CREATE TABLE transfers (
            id INTEGER PRIMARY KEY,
            filename VARCHAR NOT NULL,
            file_hash VARCHAR NOT NULL UNIQUE,
            file_size INTEGER,
            status VARCHAR,
            device VARCHAR,
            transport VARCHAR,
            duration FLOAT,
            transferred_at DATETIME
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE transfer_jobs (
            id INTEGER PRIMARY KEY,
            filepath VARCHAR NOT NULL UNIQUE,
            filename VARCHAR NOT NULL,
            file_hash VARCHAR UNIQUE,
            status VARCHAR NOT NULL,
            attempts INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
        """
    )

    connection.close()

    session_factory = create_database(database_path)

    inspector = inspect(session_factory.kw["bind"])

    transfer_columns = {
        column["name"]
        for column in inspector.get_columns("transfers")
    }

    job_columns = {
        column["name"]
        for column in inspector.get_columns("transfer_jobs")
    }

    assert {
        "attempts",
        "error",
        "started_at",
        "completed_at",
    } <= transfer_columns

    assert {
        "error",
        "started_at",
        "completed_at",
    } <= job_columns


def test_queue_persists_across_watcher_and_processor_threads(tmp_path):

    session_factory = create_database(tmp_path / "queue.db")

    queue = TransferQueue(session_factory())

    media = tmp_path / "photo.jpg"

    media.write_bytes(b"photo")

    watcher_thread = threading.Thread(
        target=queue.add,
        args=(media,)
    )

    watcher_thread.start()

    watcher_thread.join()

    assert queue.count_pending() == 1

    queued_media = queue.get_next()

    assert queued_media == media.resolve()

    assert queue.complete(queued_media)

    restarted_queue = TransferQueue(session_factory())

    assert restarted_queue.count_pending() == 0

    assert restarted_queue.count_completed() == 1


def test_queue_recovers_interrupted_job_after_restart(tmp_path):

    session_factory = create_database(tmp_path / "recovery.db")

    queue = TransferQueue(session_factory())

    media = tmp_path / "interrupted.jpg"

    media.write_bytes(b"photo")

    assert queue.add(media)

    assert queue.get_next() == media.resolve()

    restarted_queue = TransferQueue(session_factory())

    recovered_job = (
        session_factory()
        .query(TransferJob)
        .filter(TransferJob.filepath == str(media.resolve()))
        .one()
    )

    assert recovered_job.status == "pending"

    assert recovered_job.error == "Recovered after application restart"

    assert restarted_queue.count_pending() == 1


def test_queue_marks_job_failed_after_max_attempts(tmp_path):

    session_factory = create_database(tmp_path / "retries.db")

    queue = TransferQueue(session_factory())

    media = tmp_path / "retry.jpg"

    media.write_bytes(b"photo")

    assert queue.add(media)

    for _ in range(queue.MAX_ATTEMPTS):

        assert queue.get_next() == media.resolve()

        assert queue.fail(media, "ADB unavailable")

    assert queue.count_pending() == 0

    assert queue.count_failed() == 1

    assert queue.get_next() is None
