# Changelog Weaver

[![Pylint](https://github.com/hankanman/Changelog-Weaver/actions/workflows/pylint.yml/badge.svg)](https://github.com/hankanman/Changelog-Weaver/actions/workflows/pylint.yml)
[![Python package](https://github.com/Hankanman/Changelog-Weaver/actions/workflows/python-package.yml/badge.svg)](https://github.com/Hankanman/Changelog-Weaver/actions/workflows/python-package.yml)

Changelog Weaver is a powerful tool designed to automatically generate comprehensive release notes for projects hosted on Azure DevOps and GitHub. It leverages the capabilities of GPT (Generative Pre-trained Transformer) to summarize work items and produce professional, easy-to-read release notes in Markdown format.

## Features

- **Multi-Platform Support**: Seamlessly works with both Azure DevOps and GitHub repositories.
- **Automated Work Item Retrieval**: Automatically fetches work items, issues, and pull requests based on user-defined queries.
- **Intelligent Summarization**: Utilizes GPT to summarize work items into concise and meaningful release notes.
- **Multi-Format Output**: Generates release notes in Markdown and optionally converts them to HTML.
- **Customizable Configuration**: Offers customizable prompts and environment settings to fine-tune the summarization process.
- **Automation Support**: Easily integrated into CI/CD pipelines for automated release note generation.

## Example Changelog

You can see a generated changelog example [here](/assets/Changelog_Example.md)

<img src="/assets/Example_Output.png" alt="test" height="800px">

## Demo

![Demo](/assets/demo.gif)

## Setup Instructions

### Prerequisites

- **Python**: Version 3.8 or higher.
- **Azure DevOps Personal Access Token (PAT)** or **GitHub Access Token**: Required for fetching work items/issues.
- **OpenAI API Key**: Required for utilizing GPT for summarization.

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Hankanman/Changelog-Weaver.git
   cd Changelog-Weaver
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
   SOLUTION_NAME=
   RELEASE_VERSION=
   SOFTWARE_SUMMARY=
   GET_ITEM_SUMMARY=True
   GET_CHANGELOG_SUMMARY=True
   PROJECT_URL=
   QUERY=
   ACCESS_TOKEN=
   GPT_API_KEY=
   MODEL_BASE_URL=https://api.openai.com/v1
   MODEL=gpt-4o-mini
   OUTPUT_FOLDER=Releases
   LOG_LEVEL=INFO
   ```

   For GitHub projects, set the `PROJECT_URL` to your GitHub repository URL (e.g., `https://github.com/username/repo`).

### Usage

To generate release notes, run:

```bash
python -m changelog_weaver
```

This will fetch work items based on the configuration and generate a Markdown file containing the release notes.

## Platform-Specific Configuration

### Azure DevOps

- Set `PROJECT_URL` to your Azure DevOps project URL (e.g., `https://dev.azure.com/organization/project`).
- `QUERY` should be the ID of your Azure DevOps query.
- `ACCESS_TOKEN` should be your Azure DevOps Personal Access Token.

### GitHub

- Set `PROJECT_URL` to your GitHub repository URL (e.g., `https://github.com/username/repo`).
- `QUERY` can be a GitHub search query (e.g., `is:issue is:closed`).
- `ACCESS_TOKEN` should be your GitHub Personal Access Token.

## Integrating with CI/CD

You can integrate Changelog Weaver into your CI/CD pipeline using the provided Azure DevOps YAML configuration or a GitHub Actions workflow:

- **Azure DevOps**: Copy the `Changelog-Weaver-Pipeline-Azure.yaml` from the `pipelines/` directory to your project's pipeline configuration.
- **GitHub Actions**: Adjust the provided GitHub Actions YAML to suit your repository setup.

## Customization

Changelog Weaver is highly customizable. You can modify the GPT prompts in `changelog_weaver/configuration/prompts.py` to change how the release notes are generated. Additionally, the output format and details can be adjusted in `changelog_weaver/configuration/output.py`.

## Testing

Unit tests are provided and can be run using `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
