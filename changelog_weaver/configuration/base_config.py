""" Base configuration class for the project. """

import os
from pathlib import Path
from enum import Enum
import shutil
import logging

from dotenv import load_dotenv

from ..logger import get_logger

log = get_logger(__name__)


class ENVVARS(Enum):
    """Enum class for environment variables."""

    SOLUTION_NAME = "SOLUTION_NAME"
    RELEASE_VERSION = "RELEASE_VERSION"
    SOFTWARE_SUMMARY = "SOFTWARE_SUMMARY"
    GET_ITEM_SUMMARY = "GET_ITEM_SUMMARY"
    GET_CHANGELOG_SUMMARY = "GET_CHANGELOG_SUMMARY"
    INCLUDE_COMMITS = "INCLUDE_COMMITS"
    PROJECT_URL = "PROJECT_URL"
    REPO_NAME = "REPO_NAME"
    QUERY = "QUERY"
    ACCESS_TOKEN = "ACCESS_TOKEN"
    GPT_API_KEY = "GPT_API_KEY"
    MODEL_BASE_URL = "MODEL_BASE_URL"
    MODEL = "MODEL"
    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    LOG_LEVEL = "LOG_LEVEL"


class BaseConfig:
    """Base configuration class for the project."""

    def __init__(self):
        self.env = EnvironmentVariables()
        self.env.store()
        self.log_level = self.env.variables.get(ENVVARS.LOG_LEVEL, "INFO")
        self.setup_logging()
        self.valid_env = self.ensure_env_file()

    def setup_logging(self):
        """Set up the logging configuration for the project."""
        logging.getLogger("openai").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)

    def ensure_env_file(self) -> bool:
        """Ensure the .env file exists and is valid"""
        if not self.env.env_path.exists():
            default_env_path = Path(__file__).resolve().parent.parent / "defaults.env"
            if default_env_path.exists():
                shutil.copy(default_env_path, self.env.env_path)
                log.info(
                    ".env file created from defaults.env. Please complete the .env file located at: %s",
                    self.env.env_path.resolve(),
                )
                return False
            raise FileNotFoundError("Default environment file not found.")
        log.info(".env file found. Validating values...")
        if not self.validate_env_file():
            log.error(
                "Invalid .env file values. Please complete the .env file located at: %s",
                self.env.env_path.resolve(),
            )
            return False
        log.info(".env file is valid.")
        return True

    def validate_env_file(self) -> bool:
        """Ensure all required environment variables are set."""
        required_keys = ENVVARS.__members__.keys()
        missing_vars = [key for key in required_keys if not os.getenv(key)]
        if missing_vars:
            log.error(
                "Missing required environment variable(s): %s",
                ", ".join(missing_vars),
            )
            return False
        return True


class EnvironmentVariables:
    """This class manages the environment variables."""

    def __init__(self):
        self.variables = {}
        self.env_path = Path(".") / ".env"

    def store(self, env_path: Path = Path(".") / ".env"):
        """Store the environment variables."""
        self.env_path = env_path
        load_dotenv(env_path)
        for var in ENVVARS:
            value = str(os.getenv(var.value))
            if value is not None:
                self.variables[var] = value

    def retrieve(self):
        """Retrieve the environment variables."""
        for var, value in self.variables.items():
            os.environ[var] = value

    def print(self):
        """Print the environment variables."""
        for var, value in self.variables.items():
            print(f"{var}={value}")
