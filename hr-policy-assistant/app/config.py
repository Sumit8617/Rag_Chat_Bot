from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    embedding_model: str = "all-MiniLM-L6-v2"

    chroma_path: str = "./chroma_db"

    top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()