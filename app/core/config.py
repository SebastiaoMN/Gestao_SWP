from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Controle de Contratos de Software"
    environment: str = "local"
    database_url: str = "sqlite:///./software_contracts.db"
    auth_enabled: bool = True
    keycloak_issuer: str = "http://localhost:8080/realms/software-contracts"
    keycloak_client_id: str = "software-contract-control"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000"])
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SCC_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
