""" Configuration class for the application. """

import os
from pathlib import Path
from typing import Optional
import aiohttp
from dotenv import load_dotenv
from .base_config import BaseConfig
from .output import Output
from .devops import DevOps
from .prompts import Prompts
from .software import Software
from .model import Model


# pylint: disable=too-many-arguments
class Config(BaseConfig):
    """Configuration class for the application.

    Args:
        env_path (Path): The path to the .env file. Default is Path(".") / ".env".
        output_folder (str): The folder to save the output file in. Default is "Releases".
        software (Optional[Software]): The software configuration. Default is None and is self-initialized.
        devops (Optional[DevOps]): The DevOps configuration. Default is None and is self-initialized.
        model (Optional[Model]): The model configuration. Default is None and is self-initialized.
        prompts (Optional[Prompt]): The prompt configuration. Default is None and is self-initialized.
        output (Optional[Output]): The output configuration. Default is None and is self-initialized.
        log_level (str): The logging level. Default is "INFO"."""

    def __init__(
        self,
        env_path: Path = Path(".") / ".env",
        output_folder: str = "Releases",
        software: Optional[Software] = None,
        devops: Optional[DevOps] = None,
        model: Optional[Model] = None,
        prompts: Optional[Prompts] = None,
        output: Optional[Output] = None,
        log_level: str = "INFO",
    ):
        super().__init__(env_path, log_level)
        if not self.valid_env:
            return

        load_dotenv(env_path)

        output_folder = str(os.getenv("OUTPUT_FOLDER", output_folder))

        self.software = software or Software(
            name=str(os.getenv("SOLUTION_NAME")),
            version=str(os.getenv("RELEASE_VERSION")),
            brief=str(os.getenv("SOFTWARE_SUMMARY")),
        )

        self.devops = devops or DevOps(
            url=str(os.getenv("DEVOPS_BASE_URL")),
            api_version=str(os.getenv("DEVOPS_API_VERSION")),
            org=str(os.getenv("ORG_NAME")),
            project=str(os.getenv("PROJECT_NAME")),
            pat=str(os.getenv("PAT")),
            query=str(os.getenv("RELEASE_QUERY")),
        )

        self.model = model or Model(
            key=str(os.getenv("GPT_API_KEY")),
            url=str(os.getenv("MODEL_BASE_URL")),
            model_name=str(os.getenv("MODEL")),
        )

        self.prompts = prompts or Prompts(
            self.software.name,
            self.software.brief,
            self.software.brief,
        )

        self.output = output or Output(
            folder=output_folder,
            name=self.software.name,
            version=self.software.version,
        )

        self.session: aiohttp.ClientSession

    async def create_session(self):
        """Create an aiohttp session for the configuration"""
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close the aiohttp session for the configuration"""
        if self.session:
            await self.session.close()
