import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import calls, contacts, health, webhooks

settings = get_settings()

app = FastAPI(title="Prank Call Service")

app.include_router(health.router)
app.include_router(calls.router)
app.include_router(contacts.router)
app.include_router(webhooks.router)

# Serve meme sound files publicly so Twilio's <Play> can fetch them via
# the cloudflared tunnel: {PUBLIC_BASE_URL}/media/meme/<filename>
os.makedirs(settings.MEME_SOUND_DIR, exist_ok=True)
app.mount("/media/meme", StaticFiles(directory=settings.MEME_SOUND_DIR), name="meme_sounds")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
