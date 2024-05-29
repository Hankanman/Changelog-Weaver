""" Configuration module for the application. """
import os
from pathlib import Path
from dotenv import load_dotenv

# Path to the .env file
env_path = Path(".") / ".env"

# Default values for the .env file
DEFAULT_ENV = """# Azure DevOps and OpenAI Configuration
ORG_NAME=
PROJECT_NAME=
SOLUTION_NAME=
RELEASE_VERSION=
RELEASE_QUERY=
PAT=
GPT_API_KEY=
SOFTWARE_SUMMARY =
DESIRED_WORK_ITEM_TYPES = Epic,Feature,Other
OUTPUT_FOLDER = releases
MODEL=gpt-4o
MODEL_BASE_URL=https://api.openai.com/v1
DEVOPS_BASE_URL=https://dev.azure.com
DEVOPS_API_VERSION=6.0
"""

# Check if .env file exists, if not, create it with default values
if not env_path.exists():
    with open(env_path, "w", encoding="utf-8") as env_file:
        env_file.write(DEFAULT_ENV)

# Load environment variables from the .env file
load_dotenv(dotenv_path=env_path)

# Retrieve environment variables
ORG_NAME = os.getenv("ORG_NAME")
PROJECT_NAME = os.getenv("PROJECT_NAME")
SOLUTION_NAME = os.getenv("SOLUTION_NAME")
RELEASE_VERSION = os.getenv("RELEASE_VERSION")
RELEASE_QUERY = os.getenv("RELEASE_QUERY")
PAT = os.getenv("PAT")
GPT_API_KEY = os.getenv("GPT_API_KEY")
MODEL = os.getenv("MODEL")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
DEVOPS_BASE_URL = os.getenv("DEVOPS_BASE_URL")
OUTPUT_FOLDER = Path(os.getenv("OUTPUT_FOLDER"))
SOFTWARE_SUMMARY = os.getenv("SOFTWARE_SUMMARY")
DEVOPS_API_VERSION = os.getenv("DEVOPS_API_VERSION")
DESIRED_WORK_ITEM_TYPES = os.getenv("DESIRED_WORK_ITEM_TYPES").split(",")
if "Other" not in DESIRED_WORK_ITEM_TYPES:
    DESIRED_WORK_ITEM_TYPES.append("Other")

# GPT Model Data
MODEL_DATA = [
    {"Name": "gpt-3.5-turbo", "Tokens": 4096},
    {"Name": "gpt-3.5-turbo-16k", "Tokens": 16385},
    {"Name": "gpt-4", "Tokens": 8192},
    {"Name": "gpt-4-32k", "Tokens": 32768},
    {"Name": "gpt-4o", "Tokens": 128000},
]

# Prompts
SUMMARY_PROMPT = (
    f"You are a developer working on a software project called {SOLUTION_NAME}. You have been asked to review the following and write a summary "
    "of the work completed for this release. Please keep your summary to one paragraph, do not write any bullet points or list, do not group your response in any way, "
    "just a natural language explanation of what was accomplished. The following is a high-level summary of the purpose of the software for your context:\n"
)

ITEM_PROMPT = (
    "You are a developer writing a summary of the work completed for the given devops work item. Ignore timestamps and links. Return only the description text with no titles, "
    "headers, or formatting, if there is nothing to describe, return 'Addressed', always assume that the work item was completed. Do not list filenames or links. "
    "Please provide a single sentence of the work completed for the following devops work item details:\n"
)
