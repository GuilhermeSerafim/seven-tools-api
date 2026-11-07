from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    @model_validator(mode="after")
    def fix_postgres_scheme(self):
        # Render uses postgres:// but SQLAlchemy needs postgresql://
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        return self
    database_url_test: str = ""
    secret_key: str = "dev-secret-key"
    cors_origins: str = "http://localhost:8080"
    cors_origin_regex: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o"
    ai_api_key: str = ""
    clickup_api_token: str = ""
    clickup_clients_list_id: str = ""
    ai_max_tokens: int = 8192
    ai_temperature: float = 0.3
    session_ttl_days: int = 7
    login_rate_limit: str = "5/minute"
    frontend_base_url: str = "http://localhost:8080"
    password_reset_token_ttl_minutes: int = 60
    email_provider: str = "log"
    email_from: str = "SEVEN Tools <no-reply@sevendigitais.com>"
    resend_api_key: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
