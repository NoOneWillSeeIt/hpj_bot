from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, index=True)


class User(Base):
    __tablename__ = "users"

    channel: Mapped[str] = mapped_column(index=True)
    channel_id: Mapped[int] = mapped_column(index=True)
    alarm: Mapped[str | None]

    entries: Mapped[list["JournalEntry"]] = relationship(
        "JournalEntry", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )


class JournalEntry(Base):
    __tablename__ = "entries"

    date: Mapped[str]
    entry: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="entries", lazy=True)
