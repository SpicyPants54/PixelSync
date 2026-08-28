from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.migrations import migrate_database


Base = declarative_base()


def create_database(filename):

    database_path = Path(
        filename
    )

    # Create parent folders if needed
    if database_path.parent:
        database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={
            "check_same_thread": False
        }
    )

    #
    # Create any tables that do not yet exist.
    #
    Base.metadata.create_all(
        engine
    )

    #
    # Upgrade existing databases with any
    # columns introduced after the original schema.
    #
    migrate_database(
        engine
    )

    return sessionmaker(
        bind=engine
    )
