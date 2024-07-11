""" This module contains the Software class. """

from dataclasses import dataclass, field
from typing import List


@dataclass
class Software:
    """Represents a software package.
    Args:
        name (str): The name of the software package.
        version (str): The version of the software package.
        brief (str): A brief description of the software package.
        headers (List[str]): A list of headers for the software package."""

    name: str
    version: str
    brief: str
    headers: List[str] = field(default_factory=list)
    _notes: str = ""

    def add_header(self, value: str):
        """Add a header to the software package.

        Args:
            value (str): The header to add."""
        self.headers.append(value)
        return self.headers

    @property
    def notes(self):
        """Get the notes for the software package."""
        return self._notes

    @notes.setter
    def notes(self, value: str):
        self._notes += value
        return self._notes
