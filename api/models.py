# api/models.py
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, Text, DateTime

class Base(DeclarativeBase):
    pass

class Secret(Base):
    __tablename__ = "secrets"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    ciphertext: Mapped[str] = mapped_column(Text)  # base64url package (iv+ciphertext+tag)
    wrapped_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    burned: Mapped[bool] = mapped_column(Boolean, default=False)
    read_count: Mapped[int] = mapped_column(Integer, default=0)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime)
    event_type: Mapped[str] = mapped_column(String(50))
    secret_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    prev_hash: Mapped[str] = mapped_column(String(64))  # hex SHA-256
    hash: Mapped[str] = mapped_column(String(64))       # hex SHA-256
    meta_json: Mapped[str] = mapped_column(Text)
