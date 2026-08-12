from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchored to this file's location (app/config.py -> app/data/meme_sounds),
# so it resolves correctly no matter what directory the process was
# started from. A relative default here would depend on cwd at launch time,
# which isn't guaranteed to be the project root in every environment.
_DEFAULT_MEME_SOUND_DIR = str(Path(__file__).resolve().parent / "data" / "meme_sounds")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Vapi
    VAPI_PRIVATE_KEY: str
    VAPI_PUBLIC_KEY: str = ""
    VAPI_PHONE_NUMBER_ID: str
    VAPI_WEBHOOK_SECRET: str
    VAPI_WEBHOOK_URL: str

    # Deepgram
    DEEPGRAM_API_KEY: str
    DEEPGRAM_VOICE: str = "asteria"

    # OpenAI
    OPENAI_API_KEY: str

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Public URL of this server (via cloudflared tunnel), no trailing slash
    PUBLIC_BASE_URL: str = ""

    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    # Meme sound folder. Set MEME_SOUND_DIR in .env to override with an
    # absolute path if you want the audio files stored somewhere else.
    MEME_SOUND_DIR: str = _DEFAULT_MEME_SOUND_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()