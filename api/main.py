# api/main.py
from datetime import datetime, timedelta, timezone
import json
import secrets as pysecrets
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from .db import init_db, SessionLocal, append_log
from .models import Secret, AuditLog

app = FastAPI(title="OTV API", version="0.1.0")

# CORS: permitir Streamlit (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # permitir cualquier origen en dev
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

class Policy(BaseModel):
    max_reads: int = 1
    ttl_seconds: Optional[int] = Field(default=3600, ge=60, le=7*24*3600)
    canary: bool = False

class CreateSecretIn(BaseModel):
    ciphertext: str
    wrapped_key: Optional[str] = None
    policy: Policy

class CreateSecretOut(BaseModel):
    id: str

class CipherOut(BaseModel):
    ciphertext: str
    wrapped_key: Optional[str] = None

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}

@app.post("/secret", response_model=CreateSecretOut)
def create_secret(payload: CreateSecretIn):
    with SessionLocal() as db:
        secret_id = pysecrets.token_urlsafe(16)[:22]
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=payload.policy.ttl_seconds) if payload.policy.ttl_seconds else None

        rec = Secret(
            id=secret_id,
            ciphertext=payload.ciphertext,
            wrapped_key=payload.wrapped_key,
            policy_json=payload.policy.model_dump_json(),
            created_at=now,
            expires_at=expires_at,
            burned=False,
            read_count=0,
        )
        db.add(rec)
        db.commit()
        append_log(db, "create", secret_id, {"ttl_seconds": payload.policy.ttl_seconds, "max_reads": payload.policy.max_reads})
        return {"id": secret_id}

def _is_expired(rec: Secret) -> bool:
    if rec.expires_at is None:
        return False
    now = datetime.now(timezone.utc)
    exp = rec.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return now >= exp

@app.get("/s/{secret_id}", response_model=CipherOut)
def get_once(secret_id: str):
    with SessionLocal() as db:
        rec: Optional[Secret] = db.execute(select(Secret).where(Secret.id == secret_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Not found")
        if rec.burned or _is_expired(rec):
            raise HTTPException(status_code=410, detail="Gone")
        ct = rec.ciphertext
        wrapped = rec.wrapped_key
        rec.read_count += 1
        rec.burned = True
        db.commit()
        append_log(db, "read", secret_id, {"read_count": rec.read_count})
        return {"ciphertext": ct, "wrapped_key": wrapped}

@app.delete("/s/{secret_id}")
def burn_now(secret_id: str):
    with SessionLocal() as db:
        rec: Optional[Secret] = db.execute(select(Secret).where(Secret.id == secret_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Not found")
        rec.burned = True
        db.commit()
        append_log(db, "burn", secret_id, {})
        return {"ok": True}

@app.get("/log")
def export_log():
    with SessionLocal() as db:
        items = db.execute(select(AuditLog).order_by(AuditLog.id.asc())).scalars().all()
        return [
            {
                "id": it.id,
                "ts": it.ts.isoformat(),
                "event_type": it.event_type,
                "secret_id": it.secret_id,
                "prev_hash": it.prev_hash,
                "hash": it.hash,
                "meta": json.loads(it.meta_json),
            }
            for it in items
        ]
