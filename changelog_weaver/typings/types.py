"""This module contains classes for representing work items, users, and comments."""

from dataclasses import dataclass

from ..utilities import clean_string, format_date, clean_name


@dataclass
class User:
    """Represents a user."""

    display_name: str
    url: str
    user_id: str
    unique_name: str

    def __init__(self, display_name: str, url: str, user_id: str, unique_name: str):
        self.display_name = clean_name(display_name)
        self.url = url
        self.user_id = user_id
        self.unique_name = unique_name


@dataclass
class Comment:
    """Represents a comment on a work item."""

    text: str
    modified_date: str
    modified_by: User

    def __init__(self, text: str, modified_date: str, modified_by: User):
        self.text = clean_string(text, 10)
        self.modified_date = format_date(modified_date)
        self.modified_by = modified_by
