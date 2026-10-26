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

from urllib.parse import quote, urlsplit

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from app.config import get_settings

settings = get_settings()


def _public_base_url() -> str:
    base = settings.PUBLIC_BASE_URL.strip().rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
        raise ValueError("PUBLIC_BASE_URL must be a public http(s) URL with no path, query, or fragment.")
    return base


def place_meme_call(customer_phone: str, call_id: str) -> str:
    """Places the outbound call via Twilio, pointing it at our TwiML endpoint.
    Returns the Twilio Call SID."""
    base = _public_base_url()
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    twiml_url = f"{base}/webhooks/twiml/meme/{call_id}"

    call = client.calls.create(
        to=customer_phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=twiml_url,
        record=True,
        status_callback=f"{base}/webhooks/twilio-status/{call_id}",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )
    return call.sid


def build_meme_twiml(playlist: list[str]) -> str:
    """playlist is a list of filenames already in the desired random order."""
    resp = VoiceResponse()
    base = _public_base_url() if playlist else ""
    for filename in playlist:
        resp.play(f"{base}/media/meme/{quote(filename, safe='')}")
    resp.hangup()
    return str(resp)
