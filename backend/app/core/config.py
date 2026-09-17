from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cafeconnect:cafeconnect@localhost:5432/cafeconnect"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-to-a-long-random-value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    groq_api_key: str = ""
    gemini_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    gemini_model: str = "gemini-2.0-flash"
    # Conservative defaults for each provider's free tier; tune to the actual
    # published limits so we switch proactively rather than waiting for a 429.
    groq_requests_per_minute: int = 25
    gemini_requests_per_minute: int = 10

    frontend_origin: str = "http://localhost:5173"

    env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.env.lower() in ("production", "prod")


settings = Settings()

_INSECURE_JWT_SECRETS = {"change-me-to-a-long-random-value", "", "secret"}


def assert_production_secrets_are_safe(config: Settings = settings) -> None:
    """Refuse to run in production with a default/weak JWT secret.

    A secret that silently falls back to a well-known placeholder lets anyone
    forge access tokens for any user, including staff_admin — this must be a
    hard failure, not a warning, before the app is reachable on the internet.
    """
    if not config.is_production:
        return

    if config.jwt_secret in _INSECURE_JWT_SECRETS or len(config.jwt_secret) < 32:
        raise RuntimeError(
            "Refusing to start with ENV=production and an insecure/missing JWT_SECRET. "
            "Set JWT_SECRET to a random value of at least 32 characters."
        )
