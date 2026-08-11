from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


PrankType = Literal["meme_soundboard", "hiring_manager", "movie_spoiler"]


class HiringManagerInput(BaseModel):
    """All fields optional. Anything left blank falls back to a random
    AI-picked value (see prank_content.FUNNY_ROLES etc)."""

    role: Optional[str] = Field(default=None, description="Fake job title, e.g. 'Chief Vibe Officer'")
    interviewer_name: Optional[str] = Field(default=None, description="Name the AI interviewer uses")
    company_name: Optional[str] = Field(default=None, description="Fake company name")
    extra_instructions: Optional[str] = Field(
        default=None,
        description="Extra direction for the AI, e.g. specific questions to ask or a tone to use.",
    )


class MovieSpoilerInput(BaseModel):
    """All fields optional. If `user_written_story` is provided, that exact
    text is used as the disguised retelling instead of generating one with
    AI. `custom_notes` steers the AI generation when no story is supplied."""

    custom_notes: Optional[str] = Field(
        default=None,
        description="Style/focus guidance for the AI, e.g. 'focus on the twist ending' or 'tell it like gossip'.",
    )
    user_written_story: Optional[str] = Field(
        default=None,
        description="A ready-made disguised spoiler story to use as-is, skipping AI generation.",
    )


class CallCreate(BaseModel):
    contact_name: str
    contact_phone: str = Field(..., description="E.164 format, e.g. +91XXXXXXXXXX")
    context: Optional[str] = Field(
        default=None,
        description=(
            "Prank-specific context. For movie_spoiler this should be the movie title. "
            "Ignored for meme_soundboard."
        ),
    )
    prank_type: PrankType = "movie_spoiler"

    hiring_manager_input: Optional[HiringManagerInput] = Field(
        default=None, description="Optional user overrides for hiring_manager prank_type."
    )
    movie_spoiler_input: Optional[MovieSpoilerInput] = Field(
        default=None, description="Optional user overrides for movie_spoiler prank_type."
    )

    system_prompt: Optional[str] = Field(
        default=None,
        description=(
            "Pre-approved system prompt, normally obtained from POST /api/calls/preview "
            "(and possibly edited by the user). If both system_prompt and first_message "
            "are provided, no new AI content is generated -- these are used as-is. "
            "Ignored for meme_soundboard."
        ),
    )
    first_message: Optional[str] = Field(
        default=None,
        description="Pre-approved opening line, paired with system_prompt (see above).",
    )


class CallPreviewRequest(BaseModel):
    """Generates the AI script without placing a call, so the frontend can
    show it to the user for review/editing before they confirm."""

    contact_name: str
    prank_type: Literal["hiring_manager", "movie_spoiler"]
    context: Optional[str] = Field(
        default=None, description="Movie title, required when prank_type is movie_spoiler."
    )
    hiring_manager_input: Optional[HiringManagerInput] = None
    movie_spoiler_input: Optional[MovieSpoilerInput] = None


class CallPreviewResponse(BaseModel):
    prank_type: str
    system_prompt: str
    first_message: str


class CallOut(BaseModel):
    id: str
    contact_name: str
    contact_phone: str
    prank_type: str
    context: Optional[str] = None
    status: str
    vapi_call_id: Optional[str] = None
    twilio_call_sid: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    recording_url: Optional[str] = None
    success_evaluation: Optional[str] = None
    structured_data: Optional[Any] = None
    ended_reason: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OptOutRequest(BaseModel):
    phone: str = Field(..., description="E.164 phone number to add to the DNC suppression list")
    reason: Optional[str] = None
