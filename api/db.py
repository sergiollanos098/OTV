# api/db.py
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from .models import Base, Secret, AuditLog

engine = create_engine("sqlite:///otv.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Asegurar primer registro del log (genesis) si está vacío
    with SessionLocal() as db:
        count = db.execute(select(func.count(AuditLog.id))).scalar_one()
        if count == 0:
            genesis = AuditLog(
                ts=datetime.now(timezone.utc),
                event_type="genesis",
                secret_id=None,
                prev_hash="0"*64,
                hash="0"*64,
                meta_json="{}",
            )
            db.add(genesis)
            db.commit()

def _last_hash(db) -> str:
    last = db.execute(select(AuditLog).order_by(AuditLog.id.desc())).scalars().first()
    return last.hash if last else "0"*64

def append_log(db, event_type: str, secret_id: Optional[str], meta: dict):
    prev = _last_hash(db)
    payload = json.dumps({"event_type": event_type, "secret_id": secret_id, "meta": meta}, sort_keys=True)
    h = hashlib.sha256((prev + payload).encode("utf-8")).hexdigest()
    rec = AuditLog(
        ts=datetime.now(timezone.utc),
        event_type=event_type,
        secret_id=secret_id,
        prev_hash=prev,
        hash=h,
        meta_json=json.dumps(meta),
    )
    db.add(rec)
    db.commit()