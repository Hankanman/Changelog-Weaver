# Function to check if a command exists
function Find-Command {
    param (
        [string]$command
    )
    $commandPath = Get-Command $command -ErrorAction SilentlyContinue
    return $null -ne $commandPath
}

# Check for Python
if (Find-Command -command "python") {
    Write-Host "Python is installed."
}
else {
    Write-Host "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
}

# Check for pip
if (Find-Command -command "pip") {
    Write-Host "pip is installed."
}
else {
    Write-Host "pip is not installed. Please install pip from https://pip.pypa.io/en/stable/installation/"
    exit 1
}

# Check for npm
if (Find-Command -command "npm") {
    Write-Host "npm is installed."
}
else {
    Write-Host "npm is not installed. Please install npm from https://www.npmjs.com/get-npm"
    exit 1
}

# Install Python dependencies
pip install -r requirements.txt

# Check if .env file exists, if not create it with default values
if (-Not (Test-Path -Path .env)) {
    Write-Host "Creating .env file with default values."
    @"
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
"@ | Out-File -FilePath .env -Encoding utf8
}

Write-Host "Setup complete. You can now run the main script using 'python main.py'."
