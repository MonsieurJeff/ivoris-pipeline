"""
Application settings.

Loads configuration from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Settings:
    """Application configuration."""

    # Project
    PROJECT_NAME = "Ivoris Daily Extraction Pipeline"
    VERSION = "1.0.0"

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Database (SQL Server)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "1433"))
    DB_NAME = os.getenv("DB_NAME", "DentalDB")
    DB_USER = os.getenv("DB_USER", "sa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "YourStrong@Passw0rd")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    # Output
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/output"))
    OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "json")

    # Server
    PORT = int(os.getenv("PORT", "5200"))

    def validate(self) -> list[str]:
        """Validate required settings. Returns list of errors."""
        errors = []
        if not self.DB_PASSWORD:
            errors.append("DB_PASSWORD is required")
        if not self.DB_NAME:
            errors.append("DB_NAME is required")
        return errors


settings = Settings()
