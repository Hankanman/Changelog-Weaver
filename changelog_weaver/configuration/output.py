""" Output module for creating and managing output files. """

from pathlib import Path

import markdown

from ..logger import get_logger

log = get_logger(__name__)


class Output:
    """Output module for creating and managing output files.

    Args:
        folder (str): The folder to save the output file in.
        name (str): The name of the software.
        version (str): The version of the software."""

    def __init__(self, folder: str, name: str, version: str):
        self.md = True
        self.html = False
        self.pdf = False
        self.setup_file(folder, name, version)

    def setup_file(self, folder: str, name: str, version: str):
        """Setup the output file.

        Args:
            folder (str): The folder to save the output file in.
            name (str): The name of the software.
            version (str): The version of the software."""
        try:
            folder_path = Path(".") / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            self.path = (folder_path / f"{name}-v{version}.md").resolve()
            if self.path.exists():
                self.path.unlink()
            self.path.touch()
            self.setup_initial_content(name, version)
        except (FileNotFoundError, PermissionError) as e:
            log.error("Error occurred while initializing Output: %s", e)

    def setup_initial_content(self, name: str, version: str):
        """Setup the initial content of the output file.

        Args:
            name (str): The name of the software.
            version (str): The version of the software."""
        try:
            self.write(
                f"# Release Notes for {name} version v{version}\n\n"
                f"## Summary\n\n"
                f"<NOTESSUMMARY>\n\n"
                f"## Quick Links\n\n"
                f"<TABLEOFCONTENTS>\n\n"
            )
        except (FileNotFoundError, PermissionError) as e:
            log.error("Error occurred while setting up initial content: %s", e)

    def write(self, content: str):
        """Write content to the output file.

        Args:
            content (str): The content to write."""
        with open(self.path, "a", encoding="utf-8") as file_output:
            file_output.write(content)

    def read(self) -> str:
        """Read the content of the output file."""
        with open(self.path, "r", encoding="utf-8") as file:
            return file.read()

    def set_summary(self, summary: str):
        """Set the summary of the release notes.

        Args:
            summary (str): The summary to set."""
        try:
            content = self.read().replace("<NOTESSUMMARY>", summary)
            self.write(content)
        except (FileNotFoundError, PermissionError) as e:
            log.error("Error occurred while setting summary: %s", e)

    def set_toc(self, toc: str):
        """Set the table of contents for the release notes.

        Args:
            toc (str): The table of contents to set."""
        try:
            content = self.read().replace("<TABLEOFCONTENTS>", toc)
            self.write(content)
        except (FileNotFoundError, PermissionError) as e:
            log.error("Error occurred while setting table of contents: %s", e)

    async def finalize(self):
        """Finalize the output file.

        Args:
            session (aiohttp.ClientSession): The aiohttp session to use for making HTTP requests.
        """
        if self.html:
            contents = self.read()
            html_text = markdown.markdown(contents)
            file_html = self.path.with_suffix(".html")
            with open(file_html, "w", encoding="utf-8") as file:
                file.write(html_text)
