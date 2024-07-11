""" Base configuration class for the project. """

import os
from pathlib import Path
import logging as log
import shutil


class BaseConfig:
    """Base configuration class for the project."""

    def __init__(self, env_path: Path = Path(".") / ".env", log_level: str = "INFO"):
        self.env_path = env_path
        self.log_level = str(os.getenv("LOG_LEVEL", log_level))
        self.setup_logging()
        self.valid_env = self.ensure_env_file()

    def setup_logging(self):
        """Set up the logging configuration for the project."""
        log.basicConfig(
            level=self.log_level,
            format="%(levelname)s | %(message)s",
            handlers=[log.StreamHandler()],
        )
        log.getLogger("openai").setLevel(log.ERROR)
        log.getLogger("httpx").setLevel(log.ERROR)

    def ensure_env_file(self) -> bool:
        """Ensure the .env file exists and is valid"""
        if not self.env_path.exists():
            default_env_path = Path(__file__).resolve().parent.parent / "defaults.env"
            if default_env_path.exists():
                shutil.copy(default_env_path, self.env_path)
                log.info(
                    ".env file created from defaults.env. Please complete the .env file located at: %s",
                    self.env_path.resolve(),
                )
                return False
            else:
                raise FileNotFoundError("Default environment file not found.")
        else:
            log.info(".env file found. Validating values...")
            if not self.validate_env_file():
                log.error(
                    "Invalid .env file values. Please complete the .env file located at: %s",
                    self.env_path.resolve(),
                )
                return False
            log.info(".env file is valid.")
            return True

    def validate_env_file(self) -> bool:
        """Ensure all required environment variables are set."""
        required_keys = [
            "ORG_NAME",
            "PROJECT_NAME",
            "SOLUTION_NAME",
            "RELEASE_VERSION",
            "RELEASE_QUERY",
            "PAT",
            "GPT_API_KEY",
            "SOFTWARE_SUMMARY",
            "OUTPUT_FOLDER",
            "MODEL",
            "MODEL_BASE_URL",
            "DEVOPS_BASE_URL",
            "DEVOPS_API_VERSION",
            "LOG_LEVEL",
        ]
        missing_vars = [key for key in required_keys if not os.getenv(key)]
        if missing_vars:
            log.error(
                "Missing required environment variable(s): %s",
                ", ".join(missing_vars),
            )
            return False
        return True
