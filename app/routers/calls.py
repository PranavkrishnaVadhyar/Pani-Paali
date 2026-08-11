from fastapi import APIRouter, HTTPException

from app import store
from app.schemas import CallCreate, CallOut, CallPreviewRequest, CallPreviewResponse
from app.services import prank_content, vapi_service, twiml_service

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/preview", response_model=CallPreviewResponse)
def preview_call(body: CallPreviewRequest):
    """Generates the AI script (system prompt + opening line) for
    hiring_manager or movie_spoiler WITHOUT placing a call or storing
    anything, so the frontend can show it to the user first. Pass the
    returned (optionally user-edited) system_prompt/first_message into
    POST /api/calls to skip regeneration and use exactly what was shown."""

    if body.prank_type == "hiring_manager":
        overrides = body.hiring_manager_input
        script = prank_content.generate_hiring_prank_script(
            body.contact_name,
            role=overrides.role if overrides else None,
            interviewer_name=overrides.interviewer_name if overrides else None,
            company_name=overrides.company_name if overrides else None,
            extra_instructions=overrides.extra_instructions if overrides else None,
        )
    elif body.prank_type == "movie_spoiler":
        if not body.context:
            raise HTTPException(
                status_code=400,
                detail="`context` (the movie title) is required for movie_spoiler prank_type.",
            )
        overrides = body.movie_spoiler_input
        script = prank_content.generate_spoiler_script(
            body.context,
            body.contact_name,
            custom_notes=overrides.custom_notes if overrides else None,
            user_written_story=overrides.user_written_story if overrides else None,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported prank_type for preview")

    return CallPreviewResponse(
        prank_type=body.prank_type,
        system_prompt=script.system_prompt,
        first_message=script.first_message,
    )


@router.post("", response_model=CallOut)
def create_call(body: CallCreate):
    # DNC check must run before placing any call
    if store.is_suppressed(body.contact_phone):
        raise HTTPException(
            status_code=403,
            detail="This number has opted out and is on the suppression list.",
        )

    call = store.create_call(
        contact_name=body.contact_name,
        contact_phone=body.contact_phone,
        prank_type=body.prank_type,
        context=body.context,
    )
    call_id = call["id"]

    try:
        if body.prank_type == "meme_soundboard":
            call = _start_meme_call(call_id, body)
        elif body.prank_type == "hiring_manager":
            call = _start_hiring_manager_call(call_id, body)
        elif body.prank_type == "movie_spoiler":
            call = _start_movie_spoiler_call(call_id, body)
        else:
            raise HTTPException(status_code=400, detail="Unknown prank_type")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        call = store.update_call(call_id, status="failed", error=str(exc))
        raise HTTPException(status_code=502, detail=f"Failed to place call: {exc}") from exc

    return call


def _start_meme_call(call_id: str, body: CallCreate) -> dict:
    playlist = prank_content.get_random_meme_playlist()
    if not playlist:
        raise RuntimeError(
            "No meme sound files found in MEME_SOUND_DIR. Add some .mp3/.wav files."
        )
    store.update_call(call_id, structured_data={"playlist": playlist})

    sid = twiml_service.place_meme_call(body.contact_phone, call_id)
    return store.update_call(call_id, twilio_call_sid=sid, status="ringing")


def _start_hiring_manager_call(call_id: str, body: CallCreate) -> dict:
    if body.system_prompt and body.first_message:
        # User already reviewed/edited this via POST /api/calls/preview
        system_prompt, first_message = body.system_prompt, body.first_message
    else:
        overrides = body.hiring_manager_input
        script = prank_content.generate_hiring_prank_script(
            body.contact_name,
            role=overrides.role if overrides else None,
            interviewer_name=overrides.interviewer_name if overrides else None,
            company_name=overrides.company_name if overrides else None,
            extra_instructions=overrides.extra_instructions if overrides else None,
        )
        system_prompt, first_message = script.system_prompt, script.first_message

    store.update_call(call_id, system_prompt=system_prompt, first_message=first_message)

    vapi_call = vapi_service.trigger_call(body.contact_phone, system_prompt, first_message)
    return store.update_call(
        call_id, vapi_call_id=vapi_call.get("id"), status=vapi_call.get("status", "queued")
    )


def _start_movie_spoiler_call(call_id: str, body: CallCreate) -> dict:
    if not body.context:
        raise HTTPException(
            status_code=400,
            detail="`context` (the movie title) is required for movie_spoiler prank_type.",
        )
    if body.system_prompt and body.first_message:
        # User already reviewed/edited this via POST /api/calls/preview
        system_prompt, first_message = body.system_prompt, body.first_message
    else:
        overrides = body.movie_spoiler_input
        script = prank_content.generate_spoiler_script(
            body.context,
            body.contact_name,
            custom_notes=overrides.custom_notes if overrides else None,
            user_written_story=overrides.user_written_story if overrides else None,
        )
        system_prompt, first_message = script.system_prompt, script.first_message

    store.update_call(call_id, system_prompt=system_prompt, first_message=first_message)

    vapi_call = vapi_service.trigger_call(body.contact_phone, system_prompt, first_message)
    return store.update_call(
        call_id, vapi_call_id=vapi_call.get("id"), status=vapi_call.get("status", "queued")
    )


@router.get("/{call_id}", response_model=CallOut)
def get_call(call_id: str):
    call = store.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
