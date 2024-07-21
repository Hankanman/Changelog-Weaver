# Changelog Weaver (Auto-Release-Notes)

[![Pylint](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml/badge.svg)](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml)
[![Python package](https://github.com/Hankanman/Auto-Release-Notes/actions/workflows/python-package.yml/badge.svg)](https://github.com/Hankanman/Auto-Release-Notes/actions/workflows/python-package.yml)

Changelog Weaver (Auto-Release-Notes) is a powerful tool designed to automatically generate comprehensive release notes for projects in Azure DevOps. It leverages the power of GPT (Generative Pre-trained Transformer) to summarize work items and create professional, easy-to-read release notes in both Markdown and HTML formats.

## Features

- Automatic retrieval of work items from Azure DevOps
- Intelligent summarization of work items using GPT
- Generation of release notes in both Markdown and HTML formats
- Customizable prompts for GPT summarization
- Flexible deployment options (Azure DevOps Pipeline or local execution)
- Markdown linting support

## Requirements

- Python 3.7+
- Azure DevOps Personal Access Token (PAT)
- OpenAI API Key (paid)
- Node.js and npm (for optional markdownlint-cli installation)

You will need a PAID Open AI API key to run the script, support for other methods will come in future releases

## Run as Azure DevOps Pipeline

1. Copy the `Auto-Release-Notes.yml` file from [the pipelines directory of this repo](https://github.com/hankanman/Auto-Release-Notes/pipelines)
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

## Installation

### Option 1: Automated Setup

#### For Unix-based Systems

Run the `setup.sh` script:

```bash
chmod +x setup.sh
./setup.sh
```

#### For Windows

Run the `setup.ps1` PowerShell script:

```powershell
.\setup.ps1
```

These scripts will install required Python packages, install `markdownlint-cli`, and create a `.env` file with blank values if it doesn't exist.

### Option 2: Manual Setup

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

2. Install `markdownlint-cli` (optional):

```bash
npm install -g markdownlint-cli
```

3. Create a `.env` file in the project root with the following variables:

```dotenv
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

## Usage

### Running as an Azure DevOps Pipeline

1. Copy the `Auto-Release-Notes.yml` file from the `pipelines` directory to your DevOps repo.
2. Create a new pipeline in Azure DevOps, selecting "Azure Repos Git" and "Existing Azure Pipelines YAML file".
3. Set up the "Model API Key" variable with your OpenAI API key.
4. Adjust the variables in the YAML file (lines 10-20) to match your project settings.
5. Save or Save and Run the pipeline.

The pipeline will now run automatically whenever the main branch is updated.

### Running Locally

Execute the following command in your terminal:

```bash
python -m main
```

This will generate release notes in the specified output folder in both Markdown and HTML formats.

## Customization

- Modify GPT prompts by editing `SUMMARY_PROMPT` and `ITEM_PROMPT` in the `config.py` file.
- Adjust logging settings in the script for more or less detailed execution logs.

## Optional: Markdown Linting

To lint and format the generated Markdown file:

```bash
markdownlint ./Releases/*.md
```

## Contributing

We welcome contributions! If you have suggestions or improvements, please feel free to create a pull request or open an issue.

## License

This project is licensed under the MIT License.

## Acknowledgements

- This project uses the OpenAI API for GPT-based summarization.
- Thanks to all contributors who have helped shape and improve this tool.
