from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    GROQ_API_KEY: str
    YOUR_USER_ID: int
    AI_PROMPT: str = "Ты вежливый помощник. Отвечай кратко на русском."

    class Config:
        env_file = ".env"


settings = Settings()
