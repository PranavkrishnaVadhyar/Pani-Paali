import time

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from app import store
from app.config import get_settings
from app.services import twiml_service, vapi_service

router = APIRouter(tags=["webhooks"])
settings = get_settings()


# ---------------------------------------------------------------------------
# Vapi server events
# ---------------------------------------------------------------------------

@router.post("/webhooks/vapi")
async def vapi_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_vapi_secret: str | None = Header(default=None, alias="X-Vapi-Secret"),
):
    # Always verify the secret before doing anything else with the payload
    if x_vapi_secret != settings.VAPI_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()

    # Return 200 immediately; do the real work in the background
    background_tasks.add_task(_process_vapi_event, payload)
    return Response(status_code=200)


def _process_vapi_event(payload: dict) -> None:
    message = payload.get("message", payload)  # Vapi wraps events in "message"
    event_type = message.get("type")

    vapi_call = message.get("call", {}) or {}
    vapi_call_id = vapi_call.get("id")
    if not vapi_call_id:
        return

    call = store.get_call_by_vapi_id(vapi_call_id)
    if not call:
        return
    call_id = call["id"]

    if event_type == "status-update":
        status = message.get("status") or vapi_call.get("status")
        if status:
            store.update_call(call_id, status=status)

    elif event_type == "end-of-call-report":
        recording_url = message.get("recordingUrl") or message.get("artifact", {}).get("recordingUrl")
        analysis = message.get("analysis") or {}

        call = store.update_call(
            call_id,
            status="completed",
            transcript=message.get("transcript"),
            recording_url=recording_url,
            ended_reason=message.get("endedReason"),
            summary=analysis.get("summary"),
            success_evaluation=analysis.get("successEvaluation"),
            structured_data=analysis.get("structuredData") or call.get("structured_data"),
        )

        if not call.get("structured_data") and not call.get("summary"):
            # Fallback: poll Vapi directly after a short delay in case
            # the analysis wasn't ready yet when this webhook fired.
            time.sleep(5)
            try:
                fresh = vapi_service.get_call(vapi_call_id)
                fresh_analysis = fresh.get("analysis") or {}
                store.update_call(
                    call_id,
                    summary=call.get("summary") or fresh_analysis.get("summary"),
                    success_evaluation=(
                        call.get("success_evaluation") or fresh_analysis.get("successEvaluation")
                    ),
                    structured_data=call.get("structured_data") or fresh_analysis.get("structuredData"),
                    transcript=call.get("transcript") or fresh.get("transcript"),
                )
            except Exception as exc:  # noqa: BLE001
                store.update_call(call_id, error=f"Fallback poll failed: {exc}")

        # Placeholder hook: enqueue further (e.g. Groq-based) processing
        # of the transcript/summary here if you're using Groq downstream.
        _enqueue_groq_processing(call_id)

    elif event_type == "hang":
        store.update_call(call_id, status="failed", ended_reason=call.get("ended_reason") or "hang")


def _enqueue_groq_processing(call_id: str) -> None:
    """Stub: wire this up to your actual Groq-based post-processing pipeline
    (e.g. a task queue). Left as a no-op placeholder."""
    pass


# ---------------------------------------------------------------------------
# Twilio: TwiML for the meme_soundboard prank + status callback
# ---------------------------------------------------------------------------

@router.post("/webhooks/twiml/meme/{call_id}")
async def meme_twiml(call_id: str):
    call = store.get_call(call_id)
    if not call or not call.get("structured_data"):
        # Fail safe: just hang up
        twiml = twiml_service.build_meme_twiml([])
    else:
        playlist = call["structured_data"].get("playlist", [])
        twiml = twiml_service.build_meme_twiml(playlist)
    return Response(content=twiml, media_type="application/xml")


@router.post("/webhooks/twilio-status/{call_id}")
async def twilio_status(call_id: str, request: Request):
    form = await request.form()
    call_status = form.get("CallStatus")  # queued, ringing, in-progress, completed, failed...

    if store.get_call(call_id) and call_status:
        store.update_call(call_id, status=call_status)

    return Response(status_code=200)
