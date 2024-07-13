""" This module contains the Prompt class that is used to generate the prompt for the developer. """


class Prompts:
    """This class is used to generate the prompt for the developer."""

    def __init__(self, name: str, brief: str, release_notes: str):
        self._summary = f"""You are a developer working on a software project called {name}. You \
            have been asked to review the following and write a summary of the \
            work completed for this release. Please keep your summary to one \
            paragraph, do not write any bullet points or list, do not group \
            your response in any way, just a natural language explanation of \
            what was accomplished. The following is a high-level summary of the \
            purpose of the software for your context: {brief}\nThe following is \
            a high-level summary of the release notes for your context: \
            {release_notes}\n"""
        self._item = """You are a developer writing a summary of the work completed for the given \
            devops work item. Ignore timestamps and links. Return only the description \
            text with no titles, headers, or formatting, if there is nothing to \
            describe, return 'Addressed', always assume that the work item was \
            completed. Do not list filenames or links. Please provide a single sentence \
            of the work completed for the following devops work item details:\n"""

    @property
    def summary(self):
        """Get the summary prompt."""
        return self._summary

    @summary.setter
    def summary(self, value: str):
        self._summary = value

    @property
    def item(self):
        """Get the item prompt."""
        return self._item

    @item.setter
    def item(self, value: str):
        self._item = value
