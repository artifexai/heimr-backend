from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped

from database import Base, ModelUtils


class Account(Base, ModelUtils):
    __tablename__ = 'account'

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(500), nullable=False)


class UserSession(Base):
    __tablename__ = 'session'

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[str] = mapped_column(DateTime, nullable=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('account.account_id'), nullable=True, index=True)
    jwt: Mapped[str] = mapped_column(String(500), nullable=True, index=True)
    csrf: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
