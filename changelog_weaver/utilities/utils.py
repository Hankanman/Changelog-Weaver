""" This module contains utility functions for the script. """

import re
import datetime
import json
from typing import List

from ..logger import get_logger

log = get_logger(__name__)


def clean_name(text):
    """Clean the display name.

    Args:
        text (str): The display name to clean.

    Returns:
        str: The cleaned display name"""
    if isinstance(text, str):
        parts = text.split(".")
        if len(parts) == 2:
            return f"{parts[0].capitalize()} {parts[1].capitalize()}"
    return text


def create_contents(input_array: List[str]) -> str:
    """
    Converts a Array of section headers into a markdown table of contents.

    Args:
        input_array (Array[str]): The Array of section headers.

    Returns:
        str: The markdown table of contents.

    """
    markdown_links = []
    for item in input_array:
        anchor = re.sub(r"[^\w-]", "", item.replace(" ", "-")).lower()
        markdown_links.append(f"- [{item}](#{anchor})\n")
    return "".join(markdown_links)


def format_date(date) -> str:
    """Format the modified date string.

    Args:
        date (Union[str, datetime.datetime]): Input date string in the format "%Y-%m-%dT%H:%M:%S.%fZ" or datetime.datetime object.

    Returns:
        str: Human-readable date string in the format "%d-%m-%Y %H:%M"
    """
    if isinstance(date, str):
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
            return date_obj.strftime("%d-%m-%Y %H:%M")
        except ValueError:
            try:
                date_obj = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                return date_obj.strftime("%d-%m-%Y %H:%M")
            except ValueError:
                log.warning("Invalid modified date format: %s", date)
                return date
    elif isinstance(date, datetime.datetime):
        return date.strftime("%d-%m-%Y %H:%M")
    else:
        log.warning("Invalid date format: %s", date)
        return str(date)


def clean_string(string: str, min_length: int) -> str:
    """Strip a string of HTML tags, URLs, JSON, and user references."""
    if not string:
        return ""

    string = re.sub(r"<[^>]*?>", "", string)  # Remove HTML tags
    string = re.sub(r"http[s]?://\S+", "", string)  # Remove URLs
    string = re.sub(r"@\w+(\.\w+)?", "", string)  # Remove user references

    try:
        json.loads(string)
        string = ""
    except json.JSONDecodeError:
        pass

    string = string.strip()
    string = re.sub(r"&nbsp;", " ", string)
    string = re.sub(r"\s+", " ", string)

    if len(string) < min_length:
        log.debug("String is shorter than %d characters: %s", min_length, string)

    return string  # Return the string even if it's shorter than min_length
