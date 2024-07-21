""" Configuration class for the application. """

from typing import Tuple, Optional
from urllib.parse import urlparse, unquote
import logging as log

from ..typings import Project, Platform, PlatformInfo, Notes

from .base_config import BaseConfig, ENVVARS
from .output import Output
from .prompts import Prompts
from .model import Model


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
    """

    def __init__(
        self,
        model: Optional[Model] = None,
        prompts: Optional[Prompts] = None,
        output: Optional[Output] = None,
        project: Optional[Project] = None,
    ):
        super().__init__()

        env = self.env.variables

        try:
            self.project = project or parse_project(
                name=env.get(ENVVARS.SOLUTION_NAME, ""),
                version=env.get(ENVVARS.RELEASE_VERSION, ""),
                brief=env.get(ENVVARS.SOFTWARE_SUMMARY, ""),
                url=env.get(ENVVARS.PROJECT_URL, ""),
                query=env.get(ENVVARS.QUERY, ""),
                access_token=env.get(ENVVARS.ACCESS_TOKEN, ""),
            )
        except ValueError as e:
            log.error("Error parsing project: %s", str(e))
            log.error(
                "PROJECT_URL from environment: %s",
                env.get(ENVVARS.PROJECT_URL, ""),
            )
            raise

        self.model = model or Model(
            key=env.get(ENVVARS.GPT_API_KEY, ""),
            url=env.get(ENVVARS.MODEL_BASE_URL, ""),
            model_name=env.get(ENVVARS.MODEL, ""),
        )

        self.prompts = prompts or Prompts(
            self.project.name,
            self.project.brief,
            self.project.changelog.notes,
        )

        self.output = output or Output(
            folder=env.get(ENVVARS.OUTPUT_FOLDER, "Releases"),
            name=self.project.name,
            version=self.project.version,
        )


# pylint: disable=too-many-arguments
def parse_project(
    name: str, version: str, brief: str, url: str, query: str, access_token: str
) -> Project:
    """
    Extract platform information from the given URL and return a Project object.

    Args:
        url (str): The URL to analyze.

    Returns:
        Project: An object containing the project name, URL, and platform information.

    Raises:
        ValueError: If the platform cannot be determined from the URL or if required information is missing.
    """
    parsed_url = urlparse(url)

    def get_github_info() -> Tuple[str, str, str]:
        parts = parsed_url.path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        return parts[1], parts[0], f"https://github.com/{parts[0]}"

    def get_azure_devops_info() -> Tuple[str, str, str]:
        parts = parsed_url.path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid Azure DevOps URL: {url}")
        return unquote(parts[1]), parts[0], "https://dev.azure.com/"

    def get_old_azure_devops_info() -> Tuple[str, str, str]:
        parts = parsed_url.netloc.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid Azure DevOps URL: {url}")
        organization = parts[0]
        project_parts = parsed_url.path.strip("/").split("/")
        if len(project_parts) < 1:
            raise ValueError(f"Invalid Azure DevOps URL: {url}")
        return (
            unquote(project_parts[0]),
            organization,
            f"https://{organization}.visualstudio.com",
        )

    if parsed_url.netloc == "github.com":
        project_name, org, base_url = get_github_info()
        platform = Platform.GITHUB
    elif (
        parsed_url.netloc.endswith("azure.com") and "dev.azure.com" in parsed_url.netloc
    ):
        project_name, org, base_url = get_azure_devops_info()
        platform = Platform.AZURE_DEVOPS
    elif parsed_url.netloc.endswith("visualstudio.com"):
        project_name, org, base_url = get_old_azure_devops_info()
        platform = Platform.AZURE_DEVOPS
    else:
        raise ValueError(f"Unable to determine platform from URL: {url}")

    platform_info = PlatformInfo(
        platform=platform,
        organization=org,
        base_url=base_url,
        query=query,
        access_token=access_token,
    )
    return Project(
        name=name,
        ref=project_name,
        url=url,
        version=version,
        brief=brief,
        platform=platform_info,
        changelog=Notes(),
    )
