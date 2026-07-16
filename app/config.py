from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # PostgreSQL — falls back to Replit's runtime-managed PG* vars via DATABASE_URL in db.py
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = ""
    db_statement_timeout_ms: int = 8000
    db_pool_min: int = 1
    db_pool_max: int = 5

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    openai_base_url: str = "https://api.openai.com/v1"
    openai_request_timeout_s: int = 120

    # Kept short so our own timeout always fires (and returns a clean JSON
    # error) well before a hosting platform's reverse-proxy gives up on the
    # request and drops the connection first.
    openai_request_timeout_s: int = 30

    sql_max_rows: int = 200
    sql_max_repair_attempts: int = 2

    app_title: str = "Rowad Modern Engineering - SQL Data Assistant"
    app_db_path: str = "data/app.db"

    # Creates one account on first run if the user table is empty, so you're
    # never locked out. Manage further accounts with `python -m app.manage`.
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None


settings = Settings()
