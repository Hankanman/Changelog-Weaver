# Azure DevOps Release Notes Generator

[![Pylint](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml/badge.svg)](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml)

This script generates release notes for a given release version of a solution in Azure DevOps. It retrieves work items from Azure DevOps, summarizes them using GPT, and outputs the release notes in Markdown and HTML formats.

## Requirements

You will need a PAID Open AI API key to run the script, support for other methods will come in future releases

## Run as Azure DevOps Pipeline

1. Copy the `Auto-Release-Notes.yml` file from [the pipelines directory of this repo](/pipelines)
2. Add it to the DevOps Repo you wish to run the notes for, it is recommended this is on the main branch of the repo, the trigger is set to run on update of the main branch by default
3. Create a new pipeline in Azure DevOps
4. Select "Azure Repos Git"
5. Select your Repo
6. Select "Existing Azure Pipelines YAML file"
7. Select the "/Auto-Release-Notes.yml" file, this will vary depending on where you stored the file in the repo
8. Select "Continue"
9. Select "Variables" > "New Variable"
   - Name: "Model API Key"
   - Value: `<YOUR OPENAI API KEY>`
   - Keep this value secret: `True`
   - Let users override this value when running this pipeline: `True`
10. Select "OK"
11. Adjust the remaining variables in the YAML (lines 10-20):

    ```yaml
    variables:
      # The Organisation Name of the Azure DevOps organisation to use i.e. "contoso" from "https://dev.azure.com/contoso"
      ORG_NAME: "YOUR_ORG_NAME"
      # The plain text name of the project to use (not the url encoded version) i.e. "My Project" from "https://dev.azure.com/contoso/My%20Project"
      PROJECT_NAME: "YOUR_PROJECT_NAME"
      # The name of the solution. This will appear as part of the title of the notes document
      SOLUTION_NAME: "YOUR_SOLUTION_NAME"
      # The query id for the release notes query setup in Azure DevOps as a GUID i.e. "f5b6e2af-8f0c-4f6c-9a8b-3f3f2b7e0c1e" from "https://dev.azure.com/contoso/My%20Project/_queries/query/f5b6e2af-8f0c-4f6c-9a8b-3f3f2b7e0c1e"
      RELEASE_QUERY: "DEVOPS_WORK_ITEM_QUERY_GUID"
      # Describe the software or project that these release notes are for, this provides context to GPT and the notes being written
      SOFTWARE_SUMMARY: "LONG_SOFTWARE_SUMMARY"
      # The API key for the GPT service (stored as a secret) DO NOT MODIFY THE BELOW OR ENTER YOUR API KEY HERE.
      MODEL_API_KEY: $(Model API Key)
    ```

12. Hit "Save" or "Save and Run"
13. The pipeline will now run whenever the main branch is updated

## Run the Script Locally

### Prerequisites

- Python 3.7+
- Azure DevOps Personal Access Token (PAT)
- OpenAI API Key
- Node.js and npm (for optional markdownlint-cli installation)

### Dependencies

#### Automated Setup

##### Unix-based Systems

To automate the setup of the repository on Unix-based systems, run the `setup.sh` script. This script will install the required Python packages, install `markdownlint-cli`, and create a `.env` file with blank values if it does not exist.

```bash
chmod +x setup.sh
./setup.sh
```

##### Windows

To automate the setup of the repository on Windows, run the `setup.ps1` PowerShell script. This script will install the required Python packages, install `markdownlint-cli`, and create a `.env` file with blank values if it does not exist.

```powershell
.\setup.ps1
```

#### Manual Setup

If you prefer to set up the environment manually, follow these steps:

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Install `markdownlint-cli` using npm:

```bash
npm install -g markdownlint-cli
```

3. Create a `.env` file in the root directory of the project to store your secrets. This file should contain the following variables:

```dotenv
# Azure DevOps and OpenAI Configuration
ORG_NAME=
PROJECT_NAME=
SOLUTION_NAME=
RELEASE_VERSION=
RELEASE_QUERY=
PAT=
GPT_API_KEY=
MODEL=
MODEL_BASE_URL=
DEVOPS_BASE_URL=
```

If the `.env` file does not exist, it will be generated with blank values on the first load.

### Running the Script

To run the script, execute the following command in your terminal:

```bash
python -m src.main
```

The script will generate the release notes in the specified output folder in both Markdown and HTML formats.

### Optional: Markdown Linting

If you wish to lint and format the generated Markdown file, you can run the following command:

```bash
markdownlint ./Releases/*.md
```

### Customizing Prompts

You can customize the GPT prompts by editing `SUMMARY_PROMPT` and `ITEM_PROMPT` in the `config.py` file.

### Logging

The script uses Python's logging module to provide detailed logs of its execution. You can adjust the logging level in `main.py` by modifying the `setup_logs` function call.

## Contributing

If you have any suggestions or improvements, feel free to create a pull request or open an issue.

## License

This project is licensed under the MIT License.
