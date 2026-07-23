import os


def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable '{key}' is required but not set.")
    return value


class Settings:
    POSTGRES_HOST: str = require_env("POSTGRES_HOST")
    POSTGRES_PORT: int = int(require_env("POSTGRES_PORT"))
    POSTGRES_USER: str = require_env("POSTGRES_USER")
    POSTGRES_PASSWORD: str = require_env("POSTGRES_PASSWORD")
    POSTGRES_DB: str = require_env("POSTGRES_DB")

    DATABASE_URL: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


settings = Settings()
