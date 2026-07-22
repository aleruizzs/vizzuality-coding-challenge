import os


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")
