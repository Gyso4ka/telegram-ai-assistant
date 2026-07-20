"""Conversation message ORM model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, BigIntPK, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class MessageRole(enum.StrEnum):
    """Role of a stored conversation message."""

    USER = "user"
    ASSISTANT = "assistant"


class Message(Base, TimestampMixin):
    """A single turn in a user's conversation history."""

    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} user_id={self.user_id} role={self.role.value}>"
