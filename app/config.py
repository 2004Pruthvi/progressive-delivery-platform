import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "release-demo-app"
    APP_VERSION: str = "v1.0.0"
    APP_ENV: str = "development"
    COMMIT_SHA: str = "unknown"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Safeguards for failure & latency simulation (disabled by default in production)
    SIMULATION_ENABLED: bool = False
    SIMULATION_AUTH_TOKEN: str = "devops-testing-secret-token"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
