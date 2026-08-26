from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    openai_api_key: str = ""
    gemini_api_key: str = ""

    llm_provider: str = "openai"
    llm_model: str = "gpt-5-mini"

    rag_top_k: int = 5
    rag_score_threshold: float = 0.35

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()