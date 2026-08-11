"""
Quick manual test: places a single outbound call with a hardcoded system
prompt + first message, bypassing the prank_content generators, so you can
verify your Vapi + Deepgram + OpenAI + Twilio + cloudflared wiring works
end to end before building on top of it.

Usage:
    1. Make sure your FastAPI server is running locally:
         uvicorn app.main:app --reload --port 8000
    2. Make sure cloudflared is tunneling it and VAPI_WEBHOOK_URL in .env
       points at that tunnel's /webhooks/vapi.
    3. Set TEST_PHONE_NUMBER below to a real number YOU own/control and
       have consent to call.
    4. Run:  python test_call.py
    5. Then poll GET /api/calls/{id} (printed at the end) to watch status,
       transcript, and summary populate.
"""

import time

import requests

BASE_URL = "http://localhost:8000"

# !!! Replace with a real number you have consent to call for testing !!!
TEST_PHONE_NUMBER = "+91XXXXXXXXXX"

HARDCODED_SYSTEM_PROMPT = """You are a cheerful, slightly over-enthusiastic customer
support agent named Rani calling to do a routine "test call" for a phone
system upgrade. Ask the person how their day is going, confirm you can
hear them clearly, ask them to say a couple of test phrases, thank them,
and end the call warmly after about 4-5 exchanges. Keep your turns short
(1-3 sentences) so there's room for the other person to talk."""

HARDCODED_FIRST_MESSAGE = (
    "Hi there, this is Rani calling to do a quick test of our new phone "
    "system -- do you have about a minute?"
)


def main():
    # Hits the FastAPI endpoint directly with a movie_spoiler-shaped body
    # replaced by hardcoded prompt/message via a direct Vapi call path.
    # Since /api/calls always generates its own script per prank_type,
    # this script instead calls the Vapi service module directly so the
    # hardcoded prompt above is what actually gets used end-to-end.
    import sys
    sys.path.insert(0, ".")
    from app.services import vapi_service

    print("Placing test call via Vapi with hardcoded prompt...")
    result = vapi_service.trigger_call(
        customer_phone=TEST_PHONE_NUMBER,
        system_prompt=HARDCODED_SYSTEM_PROMPT,
        first_message=HARDCODED_FIRST_MESSAGE,
    )
    print("Vapi response:", result)

    vapi_call_id = result.get("id")
    print(f"\nVapi call id: {vapi_call_id}")
    print(
        "This test script calls Vapi directly, so no row is created in "
        "your local DB / no call_id from /api/calls -- use the Vapi "
        "dashboard or GET https://api.vapi.ai/call/{id} to check status, "
        "or place the call through POST /api/calls instead if you want it "
        "tracked in the app's in-memory store and via GET /api/calls/{id}."
    )


def place_via_api():
    """Alternative: places the test call through your own running FastAPI
    server (POST /api/calls) so it's tracked in the app's in-memory store, using the
    movie_spoiler prank type with a hardcoded movie as context."""
    resp = requests.post(
        f"{BASE_URL}/api/calls",
        json={
            "contact_name": "Test User",
            "contact_phone": TEST_PHONE_NUMBER,
            "prank_type": "movie_spoiler",
            "context": "Inception",
        },
        timeout=30,
    )
    resp.raise_for_status()
    call = resp.json()
    print("Created call:", call)

    call_id = call["id"]
    for _ in range(6):
        time.sleep(5)
        status_resp = requests.get(f"{BASE_URL}/api/calls/{call_id}", timeout=10)
        status_resp.raise_for_status()
        print("Status:", status_resp.json().get("status"))


if __name__ == "__main__":
    main()
    # Uncomment to instead test the full API path with DB tracking:
    # place_via_api()
