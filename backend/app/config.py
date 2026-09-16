from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-5-mini"
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
