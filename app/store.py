"""
In-memory replacement for the Postgres/SQLAlchemy layer. No persistence:
everything here lives in a plain dict for the lifetime of the process and
is gone on restart. That's fine for this app -- call state only matters
while a call is in flight or being reviewed right after.

Two things to know if you outgrow this later:
  1. It only works with a single uvicorn worker process. Multiple workers
     each get their own memory, so a call created on worker A won't be
     visible to worker B's webhook handler.
  2. Nothing survives a restart, including the DNC suppression list.
If either matters, swap this module for Redis (or Postgres again) --
routers/services only import the functions below, so that's the only
file that needs to change.
"""

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

_lock = threading.Lock()

# call_id -> call dict (mirrors app.schemas.CallOut fields)
_calls: dict[str, dict[str, Any]] = {}

# vapi_call_id -> call_id, so webhooks can look calls up by Vapi's id
_vapi_id_index: dict[str, str] = {}

# plain set of suppressed phone numbers (DNC)
_dnc: set[str] = set()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Calls
# ---------------------------------------------------------------------------

def create_call(
    contact_name: str,
    contact_phone: str,
    prank_type: str,
    context: Optional[str] = None,
) -> dict[str, Any]:
    call_id = str(uuid.uuid4())
    now = _now()
    call = {
        "id": call_id,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "prank_type": prank_type,
        "context": context,
        "status": "queued",
        "vapi_call_id": None,
        "twilio_call_sid": None,
        "system_prompt": None,
        "first_message": None,
        "transcript": None,
        "summary": None,
        "recording_url": None,
        "success_evaluation": None,
        "structured_data": None,
        "ended_reason": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    with _lock:
        _calls[call_id] = call
    return call


def get_call(call_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        call = _calls.get(call_id)
        return dict(call) if call else None


def get_call_by_vapi_id(vapi_call_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        call_id = _vapi_id_index.get(vapi_call_id)
        if not call_id:
            return None
        call = _calls.get(call_id)
        return dict(call) if call else None


def update_call(call_id: str, **fields: Any) -> Optional[dict[str, Any]]:
    with _lock:
        call = _calls.get(call_id)
        if not call:
            return None
        call.update(fields)
        call["updated_at"] = _now()
        if fields.get("vapi_call_id"):
            _vapi_id_index[fields["vapi_call_id"]] = call_id
        return dict(call)


# ---------------------------------------------------------------------------
# DNC suppression list
# ---------------------------------------------------------------------------

def is_suppressed(phone: str) -> bool:
    with _lock:
        return phone in _dnc


def add_to_dnc(phone: str, reason: Optional[str] = None) -> None:
    with _lock:
        _dnc.add(phone)
