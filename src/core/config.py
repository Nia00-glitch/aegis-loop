from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Market & Product Intelligence OS"
    app_env: str = "development"
    log_level: str = "INFO"

    research_max_iterations: int = 5
    research_time_budget_minutes: int = 30

    model_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""

    searxng_base_url: str = "http://localhost:8080"

    database_url: str = ""
    vector_db_url: str = ""
    knowledge_graph_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
