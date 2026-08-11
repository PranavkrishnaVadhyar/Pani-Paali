from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Meme sound folder (relative to app/ or absolute)
    MEME_SOUND_DIR: str = "app/data/meme_sounds"


@lru_cache
def get_settings() -> Settings:
    return Settings()
