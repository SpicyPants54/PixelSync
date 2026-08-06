from sqlalchemy import Column, Integer, String, DateTime
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

    transferred_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
 