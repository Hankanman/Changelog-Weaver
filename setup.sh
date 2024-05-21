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
# Azure DevOps and OpenAI Configuration
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
EOL
fi

echo "Setup complete. You can now run the main script using 'python3 main.py'."
