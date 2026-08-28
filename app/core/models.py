from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.core.database import Base


class Transfer(Base):

    __tablename__ = "transfers"

    id = Column(
        Integer,
        primary_key=True
    )

    filename = Column(
        String,
        nullable=False
    )

    file_hash = Column(
        String,
        unique=True,
        nullable=False
    )

    file_size = Column(
        Integer
    )

    status = Column(
        String,
        default="pending"
    )

    attempts = Column(
        Integer,
        default=0
    )

    device = Column(
        String
    )

    transport = Column(
        String
    )

    duration = Column(
        Float
    )

    error = Column(
        String
    )

    transferred_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    started_at = Column(
        DateTime
    )

    completed_at = Column(
        DateTime
    )


class TransferJob(Base):

    __tablename__ = "transfer_jobs"

    id = Column(
        Integer,
        primary_key=True
    )

    filepath = Column(
        String,
        nullable=False,
        unique=True
    )

    filename = Column(
        String,
        nullable=False
    )

    file_hash = Column(
        String,
        unique=True
    )

    status = Column(
        String,
        default="pending",
        nullable=False
    )

    attempts = Column(
        Integer,
        default=0,
        nullable=False
    )

    error = Column(
        String
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    started_at = Column(
        DateTime
    )

    completed_at = Column(
        DateTime
    )