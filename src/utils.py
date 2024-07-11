""" This module contains utility functions for the script. """

import re
import datetime
import logging as log
import json
from typing import List, Optional
import asyncio
import aiohttp

from src import Config


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


async def finalise_notes(config: Config) -> None:
    """
    Finalizes the release notes by adding the summary and table of contents.

    Args:
        html (bool): A boolean flag indicating whether to generate HTML output.
        summary_notes (str): The summary of the work items completed in this release.
        file_md (Path): The path to the output Markdown file.
        file_html (Path): The path to the output HTML file.
        section_headers (Array[str]): A Array of section headers for the table of contents.
    """
    log.info("Writing final summary and table of contents...")
    final_summary = await config.model.summarise(
        f"{config.prompts.summary}{config.software.brief}\n"
        f"The following is a summary of the work items completed in this release:\n"
        f"{config.software.notes}\nYour response should be as concise as possible",
    )

    config.output.set_summary(final_summary)
    config.output.set_toc(create_contents(config.software.headers))
    await config.output.finalize(config.session)


async def send_request(
    url: str, retries: int = 5, headers: Optional[dict] = None
) -> dict:
    """
    Send an asynchronous HTTP request and return the JSON response.

    Args:
        url (str): The URL to send the request to.
        retries (int): The number of retries in case of failure. Default is 3.
        headers (dict): The headers to include in the request. Default is None.

    Returns:
        dict: The JSON response.

    Raises:
        aiohttp.ClientError: If there is an error during the request.
    """
    if headers is None:
        headers = {}
    for _ in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.warning("Request failed: %s", str(e))
            log.info("Retrying request...")
    raise aiohttp.ClientError(f"Failed to send request after {retries} retries")
