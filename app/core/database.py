from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


def create_database(filename):

    database_path = Path(filename)

    engine = create_engine(
        f"sqlite:///{database_path}"
    )

    # Load models so SQLAlchemy knows the tables
    from app.core import models

    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine
    )