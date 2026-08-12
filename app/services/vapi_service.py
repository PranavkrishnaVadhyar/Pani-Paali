"""
Thin wrapper around the Vapi REST API (https://api.vapi.ai).

NOTE: Vapi's API surface does evolve -- double check field names against
https://docs.vapi.ai when you wire this up for real, particularly the
`server` webhook block and the `analysisPlan` shape, since those have
changed across Vapi API versions.
"""

import httpx

from app.config import get_settings

settings = get_settings()

VAPI_BASE_URL = "https://api.vapi.ai"


def build_assistant_config(system_prompt: str, first_message: str) -> dict:
    """
    Builds a transient (inline, non-persisted) assistant config for a
    single outbound call.

    Deliberately does NOT set `firstMessageMode` -- including that field
    has been observed to prevent STT from activating after the first
    message.
    """
    return {
        "firstMessage": first_message,
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
            ],
        },
        "voice": {
            "provider": "deepgram",
            # voiceId must be the bare name (e.g. "asteria"), not
            # "aura-asteria-en"
            "voiceId": settings.DEEPGRAM_VOICE,
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
        },
        "recordingEnabled": True,
        "analysisPlan": {
            "summaryPlan": {"enabled": True},
            "successEvaluationPlan": {
                "enabled": True,
                "rubric": "PassFail",
            },
        },
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 900,
        "server": {
            "url": settings.VAPI_WEBHOOK_URL,
            "secret": settings.VAPI_WEBHOOK_SECRET,
        },
    }


def trigger_call(customer_phone: str, system_prompt: str, first_message: str) -> dict:
    """Places an outbound call via Vapi. Returns the Vapi call object (dict)."""
    assistant_config = build_assistant_config(system_prompt, first_message)

    payload = {
        "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
        "customer": {"number": customer_phone},
        "assistant": assistant_config,
    }

    headers = {
        "Authorization": f"Bearer {settings.VAPI_PRIVATE_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{VAPI_BASE_URL}/call", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def get_call(vapi_call_id: str) -> dict:
    """Fetches the latest state of a call from Vapi (used as a fallback poll)."""
    headers = {"Authorization": f"Bearer {settings.VAPI_PRIVATE_KEY}"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(f"{VAPI_BASE_URL}/call/{vapi_call_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()