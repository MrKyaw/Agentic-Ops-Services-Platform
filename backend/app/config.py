"""Application configuration. All values come from the environment. Fail fast on invalid combos."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    app_name: str = "services-ai-platform"
    env: str = "local"  # local | dev | staging | prod
    log_level: str = "INFO"
    api_port: int = 8000
    auth_mode: str = "dev"  # dev | oidc
    dev_token: str = ""
    dev_tenant: str = "tenant-local-01"
    dev_roles: str = "tenant-admin"
    oidc_issuer: str = ""
    oidc_audience: str = ""
    jwks_url: str = ""
    cors_origins: str = ""
    audit_log_path: str = "audit.log.jsonl"
    database_url: str = "postgresql://postgres@127.0.0.1:5432/platform"
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    openrouter_base: str = "https://openrouter.ai/api/v1"

    @model_validator(mode="after")
    def check_auth(self) -> "Settings":
        if self.env == "prod" and self.auth_mode == "dev":
            raise ValueError("AUTH_MODE=dev is forbidden when ENV=prod")
        if self.auth_mode == "dev" and not self.dev_token and self.env != "local":
            raise ValueError("DEV_TOKEN is required when AUTH_MODE=dev outside local")
        if self.auth_mode == "oidc":
            missing = [
                k
                for k in ("oidc_issuer", "oidc_audience", "jwks_url")
                if not getattr(self, k)
            ]
            if missing:
                raise ValueError(f"AUTH_MODE=oidc requires: {', '.join(missing)}")
        if self.auth_mode not in ("dev", "oidc"):
            raise ValueError("AUTH_MODE must be dev or oidc")
        return self

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
