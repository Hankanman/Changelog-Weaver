# Function to check if a command exists
function Command-Exists {
    param (
        [string]$command
    )
    $commandPath = Get-Command $command -ErrorAction SilentlyContinue
    return $commandPath -ne $null
}

# Check for Python
if (Command-Exists -command "python") {
    Write-Host "Python is installed."
} else {
    Write-Host "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
}

# Check for pip
if (Command-Exists -command "pip") {
    Write-Host "pip is installed."
} else {
    Write-Host "pip is not installed. Please install pip from https://pip.pypa.io/en/stable/installation/"
    exit 1
}

# Check for npm
if (Command-Exists -command "npm") {
    Write-Host "npm is installed."
} else {
    Write-Host "npm is not installed. Please install npm from https://www.npmjs.com/get-npm"
    exit 1
}

# Install Python dependencies
pip install -r requirements.txt

# Check if .env file exists, if not create it with default values
if (-Not (Test-Path -Path .env)) {
    Write-Host "Creating .env file with default values."
    @"
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
"@ | Out-File -FilePath .env -Encoding utf8
}

Write-Host "Setup complete. You can now run the main script using 'python main.py'."
