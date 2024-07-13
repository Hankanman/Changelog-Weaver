""" This module contains utility functions for the script. """

import re
import datetime
import logging as log
import json
from typing import List


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


def format_date(date_str: str) -> str:
    """Format the modified date string.

    Args:
        date_str (str): Input date string in the format "%Y-%m-%dT%H:%M:%S.%fZ"

    Returns:
        str: Human-readable date string in the format "%d-%m-%Y %H:%M"
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return date_obj.strftime("%d-%m-%Y %H:%M")
    except ValueError:
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            return date_obj.strftime("%d-%m-%Y %H:%M")
        except ValueError:
            log.warning("Invalid modified date format: %s", date_str)
            return date_str


def clean_string(string: str, min_length: int = 30) -> str:
    """Strip a string of HTML tags, URLs, JSON, and user references.

    Args:
        string (str): The string to clean.
        min_length (int): The minimum length of the string to return. Default is 30.

    Returns:
        str: The cleaned string."""
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
    return string if len(string) >= min_length else ""
