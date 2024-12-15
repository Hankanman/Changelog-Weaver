#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if command_exists python3; then
    echo "Python is installed."
else
    echo "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Check for pip
if command_exists pip3; then
    echo "pip is installed."
else
    echo "pip is not installed. Please install pip from https://pip.pypa.io/en/stable/installation/"
    exit 1
fi

# Check for npm
if command_exists npm; then
    echo "npm is installed."
else
    echo "npm is not installed. Please install npm from https://www.npmjs.com/get-npm"
    exit 1
fi

# Install Python dependencies
pip3 install -r requirements.txt

# Check if .env file exists, if not create it with default values
if [ ! -f .env ]; then
    echo "Creating .env file with default values."
    cat <<EOL > .env
# This file contains the configuration settings for the Changelog-Weaver project. It is a template file and should be renamed to ".env" before use.
# The values in this file should be updated with the appropriate values for your environment.

# The name of the solution or repository. (String)
SOLUTION_NAME=
# The version of the release. (String)
RELEASE_VERSION=
# A summary of the software changes or updates. (String)
SOFTWARE_SUMMARY=
# A flag indicating whether to get the item summary. (True/False)
GET_ITEM_SUMMARY=True
# A flag indicating whether to get the changelog summary. (True/False)
GET_CHANGELOG_SUMMARY=True
# The url of the project. (String) e.g. https://dev.azure.com/ORGANISATION_NAME/PROJECT_NAME
PROJECT_URL=
# The query used to filter work items for the release. (String) e.g. 38ec490b-21e2-4eba-af3f-41ebcf231c47
QUERY=
# The Personal Access Token (PAT) for accessing Azure DevOps APIs. (String)
ACCESS_TOKEN=
# The API key for accessing the GPT API. (String)
GPT_API_KEY=
# The base URL for the GPT API. (String) e.g. https://api.openai.com/v1
MODEL_BASE_URL=https://api.openai.com/v1
# The GPT model to use for generating release notes. (String) e.g. gpt-4o-mini check https://platform.openai.com/docs/models for more models
MODEL=gpt-4o-mini
# The folder where the release notes will be generated.
OUTPUT_FOLDER=Releases
# The logging level for the application.
LOG_LEVEL=INFO
# The branch to use for fetching commits (optional)
BRANCH=main
# The starting tag for fetching commits (optional)
FROM_TAG=v1.0.0
# The ending tag for fetching commits (optional)
TO_TAG=v1.1.0
EOL
fi

echo "Setup complete. You can now run the main script using 'python3 main.py'."
