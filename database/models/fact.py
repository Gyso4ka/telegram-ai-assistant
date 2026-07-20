"""User fact ORM model — long-term memory of important facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, BigIntPK, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class UserFact(Base, TimestampMixin):
    """A durable fact the assistant should remember about a user."""

    __tablename__ = "user_facts"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_fact_key"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="facts")

    def __repr__(self) -> str:
        return f"<UserFact id={self.id} user_id={self.user_id} key={self.key!r}>"
