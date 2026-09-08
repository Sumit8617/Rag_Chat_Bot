from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_local_files_only: bool = True

    # Vector database
    chroma_path: str = "./chroma_db"

    # Retrieval
    top_k: int = 5

    # Reciprocal Rank Fusion
    rrf_k: int = 60
    rrf_vector_weight: float = 0.7
    rrf_keyword_weight: float = 0.3

    # Grounding
    grounding_max_distance: float = 0.75
    grounding_rrf_threshold_fraction: float = 0.5
    grounding_top_n_check: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()