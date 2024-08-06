# Changelog Weaver

[![Pylint](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml/badge.svg)](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml)
[![Python package](https://github.com/Hankanman/Auto-Release-Notes/actions/workflows/python-package.yml/badge.svg)](https://github.com/Hankanman/Auto-Release-Notes/actions/workflows/python-package.yml)

Changelog Weaver is a powerful tool designed to automatically generate comprehensive release notes for projects hosted on platforms like Azure DevOps and GitHub. It leverages the capabilities of GPT (Generative Pre-trained Transformer) to summarize work items and produce professional, easy-to-read release notes in Markdown format.

## Requirements

- **Automated Work Item Retrieval**: Automatically fetches work items from Azure DevOps and GitHub based on user-defined queries.
- **Intelligent Summarization**: Utilizes GPT to summarize work items into concise and meaningful release notes.
- **Multi-Format Output**: Generates release notes in Markdown and optionally converts them to HTML.
- **Customizable Configuration**: Offers customizable prompts and environment settings to fine-tune the summarization process.
- **Platform Flexibility**: Supports both Azure DevOps and GitHub for seamless integration with existing workflows.
- **Automation Support**: Easily integrated into CI/CD pipelines for automated release note generation.

## Demo

![Demo](/assets/demo.gif)

## To Do

- [x] Implement platform wrapper
- [ ] Test GitHub platform
- [ ] Write comprehensive tests
- [ ] Package into releasable executable

## Roadmap

- [ ] Pipeline yaml generators:
  - [ ] Azure DevOps
  - [ ] GitHub
- [ ] Local LLM support (Ollama)
- [ ] Ability to generate notes from commit history
- [ ] CLI for user interaction
- [ ] GUI/web app
- [ ] Platform support:
  - [ ] Jira
  - [ ] Gitlab

## Integrating with CI/CD

You can integrate Changelog Weaver into your CI/CD pipeline using the provided Azure DevOps YAML configuration or a GitHub Actions workflow:

- **Azure DevOps**: Copy the `Changelog-Weaver-Pipeline-Azure.yaml` from the `pipelines/` directory to your project’s pipeline configuration.
- **GitHub Actions**: Adjust the provided GitHub Actions YAML to suit your repository setup.

### Run as Azure DevOps Pipeline

1. Copy the `Changelog-Weaver-Pipeline-Azure.yaml` file from [the pipelines directory of this repo](/pipelines)
2. Add it to the DevOps Repo you wish to run the notes for, it is recommended this is on the main branch of the repo, the trigger is set to run on update of the main branch by default
3. Create a new pipeline in Azure DevOps
4. Select "Azure Repos Git"
5. Select your Repo
6. Select "Existing Azure Pipelines YAML file"
7. Select the "/Changelog-Weaver-Pipeline-Azure.yaml" file, this will vary depending on where you stored the file in the repo
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
      # The name of the solution or repository. (String)
      SOLUTION_NAME:
      # The version of the release. (String)
      RELEASE_VERSION:
      # A summary of the software changes or updates. (String)
      SOFTWARE_SUMMARY:
      # A flag indicating whether to get the item summary. (True/False)
      GET_ITEM_SUMMARY: True
      # A flag indicating whether to get the changelog summary. (True/False)
      GET_CHANGELOG_SUMMARY: True
      # The url of the project. (String) e.g. https://dev.azure.com/ORGANISATION_NAME/PROJECT_NAME
      PROJECT_URL:
      # The query used to filter work items for the release. (String) e.g. 38ec490b-21e2-4eba-af3f-41ebcf231c47
      QUERY:
      # The Personal Access Token (PAT) for accessing Azure DevOps APIs. (String)
      ACCESS_TOKEN:
      # The API key for accessing the GPT API. (String) (stored as a secret) DO NOT MODIFY THE BELOW OR ENTER YOUR API KEY HERE.
      GPT_API_KEY: $(Model API Key)
      # The base URL for the GPT API. (String) e.g. https://api.openai.com/v1
      MODEL_BASE_URL: https://api.openai.com/v1
      # The GPT model to use for generating release notes. (String) e.g. gpt-4o-mini check https://platform.openai.com/docs/models for more models
      MODEL: gpt-4o-mini
      # The folder where the release notes will be generated.
      OUTPUT_FOLDER: Releases
      # The logging level for the application.
      LOG_LEVEL: INFO
    ```

12. Hit "Save" or "Save and Run"
13. The pipeline will now run whenever the main branch is updated

## Setup Instructions

### Prerequisites

- **Python**: Version 3.8 or higher.
- **Azure DevOps Personal Access Token (PAT)**: Required for fetching work items from Azure DevOps.
- **GitHub Access Token**: Required for accessing GitHub repositories.
- **OpenAI API Key**: Required for utilizing GPT for summarization.

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Hankanman/Changelog-Weaver.git
   cd Auto-Release-Notes
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the root directory with the following content:

   ```bash
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
   ```

### Usage

#### Running Locally

To generate release notes, you can run the tool locally:

```bash
python -m changelog_weaver
```

This will fetch work items based on the configuration and generate a Markdown file containing the release notes.

### Customization

Changelog Weaver is highly customizable. You can modify the GPT prompts in `changelog_weaver/configuration/prompts.py` to change how the release notes are generated. Additionally, the output format and details can be adjusted in `changelog_weaver/configuration/output.py`.

### Testing

Unit tests are provided and can be run using `pytest`. To execute the tests:

```bash
pytest
```

### Contribution

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.
