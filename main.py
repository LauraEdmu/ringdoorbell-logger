from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
import psycopg
from fastapi import FastAPI, Header, HTTPException, Request

# ---------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

if not WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET not set")

app = FastAPI()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def parse_dt(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    for fmt in (
        "%B %d, %Y at %I:%M%p",
        "%B %d, %Y at %I:%M:%S%p",
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return None

def make_dedupe_key(
    event_type: str,
    device_name: str | None,
    occurred_at: datetime | None,
    payload: dict[str, Any],
) -> str:
    if occurred_at is not None:
        base = f"{event_type}|{device_name or ''}|{occurred_at.isoformat()}"
    else:
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        base = f"{event_type}|{device_name or ''}|{payload_str}"

    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------

@app.post("/ring-event")
async def ring_event(
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid json") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="json body must be an object")

    event_type = str(payload.get("event_type") or payload.get("event") or "unknown")
    device_name = payload.get("device_name") or payload.get("device") or payload.get("doorbell")
    occurred_at = parse_dt(
        payload.get("occurred_at")
        or payload.get("timestamp")
        or payload.get("event_time")
    )

    dedupe_key = make_dedupe_key(
        event_type=event_type,
        device_name=device_name if isinstance(device_name, str) else None,
        occurred_at=occurred_at,
        payload=payload,
    )

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ring_events (
                    source,
                    event_type,
                    device_name,
                    occurred_at,
                    payload,
                    dedupe_key
                )
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (dedupe_key) DO NOTHING
                RETURNING id
                """,
                (
                    "ifttt",
                    event_type,
                    device_name,
                    occurred_at,
                    json.dumps(payload),
                    dedupe_key,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "ok": True,
        "inserted": row is not None,
        "event_type": event_type,
        "device_name": device_name,
    }
