""" Configuration module for the application. """

import os
import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import aiohttp
from dotenv import load_dotenv
from .model import Model

# Default values for the .env file
DEFAULT_ENV = """
# DevOps and OpenAI Configuration
ORG_NAME=
PROJECT_NAME=
SOLUTION_NAME=
RELEASE_VERSION=
RELEASE_QUERY=
PAT=
GPT_API_KEY=
SOFTWARE_SUMMARY=
OUTPUT_FOLDER=Releases
MODEL=gpt-4o
GPT_BASE_URL=https://api.openai.com/v1
DEVOPS_BASE_URL=https://dev.azure.com
DEVOPS_API_VERSION=6.0
"""


@dataclass
class Output:
    """
    Represents an output file for the release notes.
    """

    md: bool = True
    html: bool = False
    pdf: bool = False

    def __init__(self, folder: str, name: str, version: str):
        try:
            folder_path = Path(".") / folder
            self.path = (folder_path / f"{name}-v{version}.md").resolve()
            folder_path.mkdir(parents=True, exist_ok=True)
            self.setup(name, version)
        except FileNotFoundError as e:
            print(f"Error occurred while initializing Output: {e}")
        except PermissionError as e:
            print(f"Error occurred while initializing Output: {e}")

    def setup(self, name: str, version: str):
        """Sets up the initial markdown content."""
        try:
            with open(self.path, "w", encoding="utf-8") as md_file:
                md_file.write(
                    f"# Release Notes for {name} version v{version}\n\n"
                    f"## Summary\n\n"
                    f"<NOTESSUMMARY>\n\n"
                    f"## Quick Links\n\n"
                    f"<TABLEOFCONTENTS>\n"
                )
        except FileNotFoundError as e:
            print(f"Error occurred while setting up initial content: {e}")
        except PermissionError as e:
            print(f"Error occurred while setting up initial content: {e}")

    def set_summary(self, summary: str):
        """Sets the summary of the release notes."""
        try:
            with open(self.path, "r", encoding="utf-8") as md_file:
                contents = md_file.read()
            contents = contents.replace("<NOTESSUMMARY>", summary)
            with open(self.path, "w", encoding="utf-8") as md_file:
                md_file.write(contents)
        except FileNotFoundError as e:
            print(f"Error occurred while setting summary: {e}")
        except PermissionError as e:
            print(f"Error occurred while setting summary: {e}")

    def set_toc(self, toc: str):
        """Sets the table of contents for the release notes."""
        try:
            with open(self.path, "r", encoding="utf-8") as md_file:
                contents = md_file.read()
            contents = contents.replace("<TABLEOFCONTENTS>", toc)
            with open(self.path, "w", encoding="utf-8") as md_file:
                md_file.write(contents)
        except FileNotFoundError as e:
            print(f"Error occurred while setting table of contents: {e}")
        except PermissionError as e:
            print(f"Error occurred while setting table of contents: {e}")

    async def finalize(self, session: aiohttp.ClientSession):
        """Finalizes the release notes by adding the summary and table of contents."""
        with open(self.path, "r", encoding="utf-8") as md_file:
            contents = md_file.read()
        if self.html:
            try:
                async with session.post(
                    "https://api.github.com/markdown",
                    json={"text": contents},
                    headers={"Content-Type": "application/json"},
                ) as html_response:
                    html_response.raise_for_status()
                    html_text = await html_response.text()
                    file_html = self.path.with_suffix(".html")
                    with open(file_html, "w", encoding="utf-8") as file:
                        file.write(html_text)
            except aiohttp.ClientError as e:
                print(f"Error occurred while making HTTP request: {e}")


@dataclass
class DevOps:
    """
    Configuration class for the DevOps API.

    Attributes:
        devops_base_url (str): The base URL for the DevOps API.
        devops_api_version (str): The version of the DevOps API.
        org (str): The organization name.
        project (str): The project name.
        pat (str): The personal access token for the DevOps API.
        query (str): The query for fetching release work items.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        url: str,
        api_version: str,
        org: str,
        project: str,
        query: str,
        pat: str,
    ):
        self.url = url
        self.api_version = api_version
        self.org = org
        self.project = project
        self.query = query
        self.pat = base64.b64encode(f":{pat}".encode()).decode()

    fields: List[str] = field(
        default_factory=lambda: [
            "System.Title",
            "System.Id",
            "System.State",
            "System.Tags",
            "System.Description",
            "System.Parent",
            "System.CommentCount",
            "System.WorkItemType",
            "Microsoft.VSTS.Common.Priority",
            "Microsoft.VSTS.TCM.ReproSteps",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "Microsoft.VSTS.Scheduling.StoryPoints",
        ]
    )


class Prompt:
    """
    Represents the prompts for the application.

    Attributes:
        summary (str): The prompt for summarizing the work.
        item (str): The prompt for summarizing a work item.
    """

    def __init__(self, name: str, brief: str, release_notes: str):
        self._summary = (
            f"You are a developer working on a software project called {name}. You have been asked to review the following and write a summary "
            f"of the work completed for this release. Please keep your summary to one paragraph, do not write any bullet points or list, do not group your response in any way, "
            f"just a natural language explanation of what was accomplished. The following is a high-level summary of the purpose of the software for your context: {brief}\n"
            f"The following is a high-level summary of the release notes for your context: {release_notes}\n"
        )
        self._item = (
            "You are a developer writing a summary of the work completed for the given devops work item. Ignore timestamps and links. Return only the description text with no titles, "
            "headers, or formatting, if there is nothing to describe, return 'Addressed', always assume that the work item was completed. Do not list filenames or links. "
            "Please provide a single sentence of the work completed for the following devops work item details:\n"
        )

    @property
    def summary(self):
        """Returns the summary prompt."""
        return self._summary

    @summary.setter
    def summary(self, value: str):
        """Sets the summary prompt."""
        self._summary = value

    @property
    def item(self):
        """Returns the item prompt."""
        return self._item

    @item.setter
    def item(self, value: str):
        """Sets the item prompt."""
        self._item = value


@dataclass
class Software:
    """
    Represents the software configuration settings.

    Attributes:
        name (str): The name of the solution.
        version (str): The version of the release.
        output_folder (Path): The output folder for the release notes.
        brief (str): The summary of the software.
    """

    name: str
    version: str
    brief: str
    headers: List[str] = field(default_factory=list)

    def add_header(self, value: str):
        """Adds a header to the software."""
        self.headers.append(value)
        return self.headers

    @property
    def notes(self):
        """Returns the notes for the software."""
        return self.notes

    @notes.setter
    def notes(self, value: str):
        """Sets the notes for the software."""
        self.notes = self.notes + value


@dataclass
class Config:
    """
    Master configuration class for the application.

    Attributes:
        software (Software): The software configuration settings.
        devops (DevOpsConfig): The configuration for the DevOps API.
        model (ModelConfig): The configuration for the GPT model.
        prompts (Prompts): The prompts for the application.
        output (Output): The output file configuration.
    """

    software: Software
    devops: DevOps
    model: Model
    prompts: Prompt
    output: Output

    # pylint: disable=too-many-arguments
    @classmethod
    def create(
        cls,
        env_path: Path = Path(".") / ".env",
        output_folder: str = "Releases",
        software: Optional[Software] = None,
        devops: Optional[DevOps] = None,
        model: Optional[Model] = None,
        prompts: Optional[Prompt] = None,
        output: Optional[Output] = None,
    ) -> "Config":
        """Creates a new configuration object."""
        # Check if .env file exists, if not, create it with default values
        if not env_path.exists():
            try:
                with open(env_path, "w", encoding="utf-8") as env_file:
                    env_file.write(DEFAULT_ENV)
            except FileNotFoundError as e:
                print(f"Error occurred while creating .env file: {e}")
            except PermissionError as e:
                print(f"Error occurred while creating .env file: {e}")

        # Load environment variables from the .env file
        load_dotenv(env_path)

        # Set default output folder if not provided
        if output_folder is None:
            output_folder = str(os.getenv("OUTPUT_FOLDER", "Releases"))

        if software is None:
            software = Software(
                name=str(os.getenv("SOLUTION_NAME")),
                version=str(os.getenv("RELEASE_VERSION")),
                brief=str(os.getenv("SOFTWARE_SUMMARY")),
            )

        if devops is None:
            devops = DevOps(
                url=str(os.getenv("DEVOPS_BASE_URL")),
                api_version=str(os.getenv("DEVOPS_API_VERSION")),
                org=str(os.getenv("ORG_NAME")),
                project=str(os.getenv("PROJECT_NAME")),
                pat=str(os.getenv("PAT")),
                query=str(os.getenv("RELEASE_QUERY")),
            )

        if model is None:
            model = Model(
                key=str(os.getenv("GPT_API_KEY")),
                url=str(os.getenv("GPT_BASE_URL")),
                model_name=str(os.getenv("MODEL")),
            )

        if prompts is None:
            prompts = Prompt(
                software.name,
                software.brief,
                software.brief,
            )

        if output is None:
            output = Output(
                folder=output_folder,
                name=software.name,
                version=software.version,
            )

        return cls(
            software=software,
            devops=devops,
            model=model,
            prompts=prompts,
            output=output,
        )

    def write(self, content: str):
        """Appends content to the Markdown file."""
        with open(self.output.path, "a", encoding="utf-8") as file_output:
            file_output.write(content)

    def read(self) -> str:
        """Reads the contents of a file and returns it as a string."""
        with open(self.output.path, "r", encoding="utf-8") as file:
            contents = file.read()
        return contents
