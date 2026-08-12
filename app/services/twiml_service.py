"""
The meme_soundboard prank doesn't need an AI conversation -- it's just a
random-order playback of local audio clips. Vapi is overkill (and its
LLM/STT loop isn't a fit) for "play some sounds," so this prank type
places the call directly via Twilio's REST API and points Twilio at our
own /webhooks/twiml/meme/{call_id} endpoint, which returns TwiML that
<Play>s each clip in the randomized order chosen at call-creation time.

Audio files must be reachable at a public URL for Twilio's <Play> to
fetch them, so they're served from this app under /media/meme/<filename>
via the cloudflared tunnel (PUBLIC_BASE_URL).
"""

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from app.config import get_settings

settings = get_settings()


def place_meme_call(customer_phone: str, call_id: str) -> str:
    """Places the outbound call via Twilio, pointing it at our TwiML endpoint.
    Returns the Twilio Call SID."""
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    twiml_url = f"{settings.PUBLIC_BASE_URL}/webhooks/twiml/meme/{call_id}"

    call = client.calls.create(
        to=customer_phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=twiml_url,
        record=True,
        status_callback=f"{settings.PUBLIC_BASE_URL}/webhooks/twilio-status/{call_id}",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )
    return call.sid


def build_meme_twiml(playlist: list[str]) -> str:
    """playlist is a list of filenames already in the desired random order."""
    resp = VoiceResponse()
    base = settings.PUBLIC_BASE_URL
    for filename in playlist:
        resp.play(f"{base}/media/meme/{filename}")
    resp.hangup()
    return str(resp)