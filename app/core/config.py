from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central place for all configuration. Never read os.getenv() directly
    elsewhere in the app — import `settings` from here instead.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    # NOTE: override secret_key via .env in any non-dev environment — JWTs
    # are only as safe as this value.
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///./dev.db"

    # Gemini (Phase 4+)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Gemini embeddings, for RAG over policy docs (Phase 6)
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    # Company policy placeholders — confirm real values with the business
    # before relying on these in the chatbot (Phase 5/6).
    office_open_time: str = "09:00"
    office_close_time: str = "18:00"
    working_days: str = "Mon,Tue,Wed,Thu,Fri"
    annual_vacation_days: int = 21


settings = Settings()
