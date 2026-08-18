from sqlalchemy import Column, Integer, String, DateTime, Float

from datetime import datetime

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
        String
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


    transferred_at = Column(
        DateTime,
        default=datetime.utcnow
    )



class TransferJob(Base):

    __tablename__ = "transfer_jobs"


    id = Column(
        Integer,
        primary_key=True
    )


    filepath = Column(
        String,
        nullable=False
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
        default="pending"
    )


    attempts = Column(
        Integer,
        default=0
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )