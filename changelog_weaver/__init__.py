""" Main Package Init """

from pathlib import Path


def generate_env_file():
    """Generate the .env file if it doesn't exist."""
    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        default_content = """
# This file contains the configuration settings for the Auto-Release-Notes project. It is a template file and should be renamed to ".env" before use.
# The values in this file should be updated with the appropriate values for your environment.

# The name of the solution or repository.
SOLUTION_NAME=
# The version of the release.
RELEASE_VERSION=
# A summary of the software changes or updates.
SOFTWARE_SUMMARY=
# The url of the project.
PROJECT_URL=
# The query used to filter work items for the release.
QUERY=
# The Personal Access Token (PAT) for accessing Azure DevOps APIs.
ACCESS_TOKEN=
# The API key for accessing the GPT API.
GPT_API_KEY=
# The base URL for the GPT API.
MODEL_BASE_URL=https://api.openai.com/v1
# The GPT model to use for generating release notes.
MODEL=gpt-4o
# The folder where the release notes will be generated.
OUTPUT_FOLDER=Releases
# The logging level for the application.
LOG_LEVEL=INFO
"""
        with open(env_path, "w", encoding="utf-8") as env_file:
            env_file.write(default_content.strip())
        print(f".env file generated at {env_path}")
    else:
        print(".env file already exists")


# Call the function to generate the .env file when the module is imported
generate_env_file()
