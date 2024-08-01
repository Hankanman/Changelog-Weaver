# Changelog Weaver

[![Pylint](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml/badge.svg)](https://github.com/hankanman/Auto-Release-Notes/actions/workflows/pylint.yml)
[![Python package](https://github.com/Hankanman/Auto-Release-Notes/actions/workflows/python-package.yml/badge.svg)](https://github.com/Hankanman/Auto-Release-Notes/actions/workflows/python-package.yml)

Changelog Weaver (Auto-Release-Notes) is a powerful tool designed to automatically generate comprehensive release notes for projects hosted on platforms like Azure DevOps and GitHub. It leverages the capabilities of GPT (Generative Pre-trained Transformer) to summarize work items and produce professional, easy-to-read release notes in Markdown format.

## Features

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
- [ ] Config migration
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

## Setup Instructions

### Prerequisites

- **Python**: Version 3.8 or higher.
- **Azure DevOps Personal Access Token (PAT)**: Required for fetching work items from Azure DevOps.
- **GitHub Access Token**: Required for accessing GitHub repositories.
- **OpenAI API Key**: Required for utilizing GPT for summarization.

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/hankanman/Auto-Release-Notes.git
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
   SOLUTION_NAME=YourSolutionName
   RELEASE_VERSION=1.0.0
   SOFTWARE_SUMMARY=Brief description of your software
   GET_ITEM_SUMMARY=True
   GET_CHANGELOG_SUMMARY=True
   PROJECT_URL=https://dev.azure.com/your-org/your-project
   QUERY=YourQueryID
   ACCESS_TOKEN=YourAzureDevOpsPAT
   GPT_API_KEY=YourOpenAIApiKey
   MODEL_BASE_URL=https://api.openai.com/v1
   MODEL=gpt-4
   OUTPUT_FOLDER=Releases
   LOG_LEVEL=INFO
   ```

### Usage

#### Running Locally

To generate release notes, you can run the tool locally:

```bash
python -m changelog_weaver
```

This will fetch work items based on the configuration and generate a Markdown file containing the release notes.

#### Integrating with CI/CD

You can integrate Changelog Weaver into your CI/CD pipeline using the provided Azure DevOps YAML configuration or a GitHub Actions workflow:

- **Azure DevOps**: Copy the `Auto-Release-Notes.yaml` from the `pipelines/` directory to your project’s pipeline configuration.
- **GitHub Actions**: Adjust the provided GitHub Actions YAML to suit your repository setup.

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
