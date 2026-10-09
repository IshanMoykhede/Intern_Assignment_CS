import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from app.db.database import Base


class ChatSession(Base):
    __tablename__ = "sessions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )