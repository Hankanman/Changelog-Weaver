""" Configuration module for the application. """

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv
import aiohttp

# Path to the .env file
env_path = Path(".") / ".env"

# Default values for the .env file
DEFAULT_ENV = """# DevOps and OpenAI Configuration
ORG_NAME=
PROJECT_NAME=
SOLUTION_NAME=
RELEASE_VERSION=
RELEASE_QUERY=
PAT=
GPT_API_KEY=
SOFTWARE_SUMMARY=
DESIRED_WORK_ITEM_TYPES=Epic,Feature
OUTPUT_FOLDER=Releases
MODEL=gpt-4o
GPT_BASE_URL=https://api.openai.com/v1
DEVOPS_BASE_URL=https://dev.azure.com
DEVOPS_API_VERSION=6.0
"""

# Check if .env file exists, if not, create it with default values
if not env_path.exists():
    with open(env_path, "w", encoding="utf-8") as env_file:
        env_file.write(DEFAULT_ENV)

# Load environment variables from the .env file
load_dotenv(env_path)


@dataclass
class Config:
    """
    Configuration class for the application.

    Attributes:
        solution_name (str): The name of the solution.
        release_version (str): The version of the release.
        output_folder (Path): The output folder for the release notes.
        software_summary (str): The summary of the software.
    """

    solution_name = str(os.getenv("SOLUTION_NAME"))
    release_version = str(os.getenv("RELEASE_VERSION"))
    output_folder = Path(str(os.getenv("OUTPUT_FOLDER")))
    if output_folder is None:
        output_folder = Path("Releases")
    software_summary = str(os.getenv("SOFTWARE_SUMMARY"))


@dataclass
class DevOpsConfig:
    """
    Configuration class for the DevOps API.

    Attributes:
        devops_base_url (str): The base URL for the DevOps API.
        devops_api_version (str): The version of the DevOps API.
        org_name (str): The organization name.
        project_name (str): The project name.
        pat (str): The personal access token for the DevOps API.
        release_query (str): The query for fetching release work items.
    """

    devops_base_url = str(os.getenv("DEVOPS_BASE_URL"))
    devops_api_version = str(os.getenv("DEVOPS_API_VERSION"))
    org_name = str(os.getenv("ORG_NAME"))
    project_name = str(os.getenv("PROJECT_NAME"))
    pat = str(os.getenv("PAT"))
    release_query = str(os.getenv("RELEASE_QUERY"))
    parent_work_item_types = [
        item.strip() for item in str(os.getenv("DESIRED_WORK_ITEM_TYPES")).split(",")
    ]
    if "Other" not in parent_work_item_types:
        parent_work_item_types.append("Other")
    fields = [
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


@dataclass
class ModelConfig:
    """
    Configuration class for the GPT model.

    Attributes:
        gpt_api_key (str): The API key for the GPT model.
        gpt_base_url (str): The base URL for the GPT model.
        model (str): The name of the GPT model.
        models (List[Dict[str, Any]]): A list of available GPT models.
    """

    gpt_api_key = str(os.getenv("GPT_API_KEY"))
    gpt_base_url = str(os.getenv("MODEL_BASE_URL"))
    model = str(os.getenv("MODEL"))
    # GPT Model Data
    models = [
        {"Name": "gpt-3.5-turbo", "Tokens": 4096},
        {"Name": "gpt-3.5-turbo-16k", "Tokens": 16385},
        {"Name": "gpt-4", "Tokens": 8192},
        {"Name": "gpt-4-32k", "Tokens": 32768},
        {"Name": "gpt-4o", "Tokens": 128000},
    ]


@dataclass
class GroupConfig:
    """
    Represents the configuration for updating a group of work items.

    Attributes:
        summary_notes_ref (str): The reference to the summary notes.
        grouped_work_items (Object[str, Array[Object[str, Any]]]): A Objectionary containing grouped work items.
        work_item_icon (Object[str, Any]): A Objectionary containing work item icons.
        file_md (Path): The path to the markdown file.
        session (aiohttp.ClientSession): The client session for making HTTP requests.
        summarize_items (bool): A flag indicating whether to summarize the items.
    """

    summary_notes_ref: str
    grouped_work_items: Dict[str, List[Any]]
    work_item_icon: Dict[str, Any]
    file_md: Path
    session: aiohttp.ClientSession
    summarize_items: bool


@dataclass
class Prompts:
    """
    Represents the prompts for the application.

    Attributes:
        SUMMARY_PROMPT (str): The prompt for summarizing the work.
        ITEM_PROMPT (str): The prompt for summarizing a work item.
    """

    # Prompts
    summary = str(
        f"You are a developer working on a software project called {Config.solution_name}. You have been asked to review the following and write a summary "
        "of the work completed for this release. Please keep your summary to one paragraph, do not write any bullet points or list, do not group your response in any way, "
        "just a natural language explanation of what was accomplished. The following is a high-level summary of the purpose of the software for your context:\n"
    )

    item = str(
        "You are a developer writing a summary of the work completed for the given devops work item. Ignore timestamps and links. Return only the description text with no titles, "
        "headers, or formatting, if there is nothing to describe, return 'Addressed', always assume that the work item was completed. Do not list filenames or links. "
        "Please provide a single sentence of the work completed for the following devops work item details:\n"
    )
