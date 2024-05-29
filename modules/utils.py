# utils.py
import asyncio
import aiohttp
import re
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from modules.enums import (
    WorkItemType,
    LogLevel,
    WorkItemField,
    ResponseStatus,
    APIEndpoint,
)
from modules.config import (
    DEVOPS_BASE_URL,
    MODEL_BASE_URL,
    SUMMARY_PROMPT,
    SOFTWARE_SUMMARY,
    GPT_API_KEY,
    MODEL,
    MODEL_DATA,
    ITEM_PROMPT,
)


@dataclass
class WorkItem:
    """
    Represents a work item.

    Attributes:
        id (int): The ID of the work item.
        url (str): The URL of the work item.
        title (str): The title of the work item.
        repro (str): The repro steps of the work item.
        description (str): The description of the work item.
        comments (str): The comments on the work item.
    """

    id: int
    url: str
    title: str
    repro: str
    description: str
    comments: str


@dataclass
class Config:
    """
    Represents the configuration settings for the script.

    Attributes:
        org_name (str): The name of the organization.
        project_name (str): The name of the project.
        pat (str): The personal access token for authentication.
        gpt_api_key (str): The API key for the GPT service.
        model (str): The name of the model.
        model_base_url (str): The base URL for the model.
        desired_work_item_types (List[WorkItemType]): A list of desired work item types.
        output_folder (Path): The path to the output folder.
        software_summary (str): A summary of the software.
    """

    org_name: str
    project_name: str
    pat: str
    gpt_api_key: str
    model: str
    model_base_url: str
    desired_work_item_types: List[WorkItemType]
    output_folder: Path
    software_summary: str


def setupLogs(level: LogLevel = LogLevel.INFO):
    """
    Sets up logging configuration with the specified logging level.

    Parameters:
        level (LogLevel): The logging level to set. Defaults to LogLevel.INFO.

    Returns:
        None
    """
    logging.basicConfig(
        level=level.value, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def createContents(input_array: List[str]) -> str:
    """
    Converts a list of section headers into a markdown table of contents.

    Args:
        input_array (List[str]): The list of section headers.

    Returns:
        str: The markdown table of contents.

    """
    markdown_links = []
    for item in input_array:
        anchor = re.sub(r"[^\w-]", "", item.replace(" ", "-")).lower()
        markdown_links.append(f"- [{item}](#{anchor})\n")
    return "".join(markdown_links)


def cleanString(text: str) -> str:
    """
    Removes non-alphanumeric characters from a string.

    Args:
        text (str): The input string to be cleaned.

    Returns:
        str: The cleaned string with non-alphanumeric characters removed.
    """
    text = re.sub(r"<img[^>]+>", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)
    text = re.sub(r'data:image\/[^;]+;base64,[^\s"]+', "", text)
    return re.sub(r"[^a-zA-Z0-9 ]", "", text)


def countTokens(text: str) -> int:
    """
    Calculates the token count for a given text.

    Parameters:
    text (str): The input text for which the token count needs to be calculated.

    Returns:
    int: The total count of tokens in the given text.
    """
    word_count = len(re.findall(r"\b\w+\b", text))
    char_count = len(re.sub(r"\s", "", text))
    return word_count + char_count


async def summarise(prompt: str):
    """
    Sends a prompt to GPT and returns the response.

    Args:
        prompt (str): The prompt to be sent to GPT.

    Returns:
        str: The response generated by GPT.
    """
    model_objects = {model["Name"]: model for model in MODEL_DATA}
    model_object = model_objects.get(MODEL)
    token_count = countTokens(prompt)
    if model_object and token_count > model_object["Tokens"]:
        logging.warning(
            f"The prompt contains too many tokens for the selected model {token_count}/{model_object['Tokens']}. Please reduce the size of the prompt."
        )
        return "Prompt too large"

    retry_count = 0
    initial_delay = 10
    max_retries = 6
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GPT_API_KEY}",
    }
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}

    async with aiohttp.ClientSession(headers=headers) as session:
        while retry_count <= max_retries:
            try:
                async with session.post(
                    MODEL_BASE_URL + APIEndpoint.COMPLETIONS.value, json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
            except aiohttp.ClientResponseError as e:
                if e.status == ResponseStatus.RATE_LIMIT.value:
                    delay = initial_delay * (2**retry_count)
                    logging.warning(f"AI API Error (Too Many Requests), retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    retry_count += 1
                elif e.status == ResponseStatus.ERROR.value:
                    delay = initial_delay * (2**retry_count)
                    logging.warning(
                        f"AI API Error (Internal Server Error), retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                    retry_count += 1
                elif e.status == ResponseStatus.NOT_FOUND.value:
                    delay = initial_delay * (2**retry_count)
                    logging.warning(
                        f"AI API Error (Not Found), retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                    retry_count += 1
                else:
                    logging.error("Request failed", exc_info=True)
                    raise e


async def getWorkItemIcons(
    session: aiohttp.ClientSession, org_name: str, project_name: str
) -> Dict[str, Any]:
    """
    Fetches work item icons from Azure DevOps.

    Args:
        session (aiohttp.ClientSession): The aiohttp client session.
        org_name (str): The name of the organization in Azure DevOps.
        project_name (str): The name of the project in Azure DevOps.

    Returns:
        Dict[str, Any]: A dictionary containing the work item icons.

    """
    uri = DEVOPS_BASE_URL + APIEndpoint.WORK_ITEM_TYPES.value.format(
        org_name=org_name, project_name=project_name
    )
    async with session.get(uri) as response:
        response_json = await response.json()
        icons = [
            {"name": item["name"], "iconUrl": item["icon"]["url"]}
            for item in response_json["value"]
        ]
        workItemIcon = {}
        for icon in icons:
            color_match = re.search(r"color=([a-zA-Z0-9]+)", icon["iconUrl"])
            color = color_match.group(1) if color_match else None
            workItemIcon[icon["name"]] = {"iconUrl": icon["iconUrl"], "color": color}

        # Ensure "Other" work item type has a default icon
        workItemIcon[WorkItemType.OTHER.value] = workItemIcon.get(
            WorkItemType.OTHER.value,
            {
                "iconUrl": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_clipboard_issue?color=577275&v=2",
                "color": "577275",
            },
        )
        return workItemIcon


async def getWorkItems(
    session: aiohttp.ClientSession, org_name: str, project_name: str, query_id: str
) -> List[Dict[str, Any]]:
    """
    Fetches work items from Azure DevOps based on a query.

    Args:
        session (aiohttp.ClientSession): The aiohttp client session.
        org_name (str): The name of the organization in Azure DevOps.
        project_name (str): The name of the project in Azure DevOps.
        query_id (str): The ID of the query to fetch work items from.

    Returns:
        List[Dict[str, Any]]: A list of work items fetched from Azure DevOps.
    """
    uri = DEVOPS_BASE_URL + APIEndpoint.WIQL.value.format(
        org_name=org_name, project_name=project_name, query_id=query_id
    )
    async with session.get(uri) as response:
        query_response = await response.json()
        if response.status != 200:
            logging.error(query_response["message"])
            exit(1)
        ids = [str(item["id"]) for item in query_response["workItems"]]

        # Split ids into chunks of 199
        chunks = [ids[i:i + 199] for i in range(0, len(ids), 199)]

        # Fetch work items in batches
        work_items = []
        for chunk in chunks:
            ids_str = ",".join(chunk)
            work_items_chunk = await fetch_work_items(session, org_name, project_name, ids_str)
            work_items.extend(work_items_chunk)

        print(f"Found {len(work_items)} work items")
        return work_items
    
async def fetch_work_items(session, org_name: str, project_name: str, ids: List[str]):
    uri = DEVOPS_BASE_URL + APIEndpoint.WORK_ITEMS.value.format(
        org_name=org_name, project_name=project_name, ids=ids
    )
    async with session.get(uri) as response:
        work_items_response = await response.json()
        return work_items_response["value"]

async def updateItemGroup(
    summary_notes_ref: str,
    grouped_work_items: Dict[str, List[Dict[str, Any]]],
    workItemIcon: Dict[str, Any],
    file_md: Path,
    session: aiohttp.ClientSession,
    summarize_items: bool,
) -> None:
    """
    Updates the release notes with details of grouped work items.

    Args:
        summary_notes_ref (str): The reference to the summary notes.
        grouped_work_items (Dict[str, List[Dict[str, Any]]]): A dictionary containing the grouped work items.
        workItemIcon (Dict[str, Any]): A dictionary containing the work item icons.
        file_md (Path): The path to the output file.
        session (aiohttp.ClientSession): The aiohttp client session.
        summarize_items (bool): A flag indicating whether to summarize the items.

    Returns:
        None
    """
    for work_item_type, items in grouped_work_items.items():
        logging.info(f" Writing notes for {work_item_type}s")
        group_icon_url = workItemIcon[work_item_type]["iconUrl"]
        summary_notes_ref += f" - {work_item_type}s: \n"

        with open(file_md, "a", encoding="utf-8") as file:
            file.write(
                f"### <img src='{group_icon_url}' alt='icon' width='12' height='12'> {work_item_type}s\n"
            )

        for child_item in items:
            id = child_item["id"]
            url = child_item["_links"]["html"]["href"]
            title = cleanString(child_item["fields"][WorkItemField.TITLE.value])
            repro = cleanString(
                child_item["fields"].get(WorkItemField.REPRO_STEPS.value, "")
            )
            description = cleanString(
                child_item["fields"].get(WorkItemField.DESCRIPTION.value, "")
            )
            comments = ""

            if "_links" in child_item and "workItemComments" in child_item["_links"]:
                comment_link = child_item["_links"]["workItemComments"]["href"]
                async with session.get(comment_link) as comment_response:
                    comments_response = await comment_response.json()
                    comments = " ".join(
                        [
                            cleanString(comment["text"])
                            for comment in comments_response.get("comments", [])
                        ]
                    )

            if summarize_items:
                summary = await summarise(
                    f"{ITEM_PROMPT}: {title} {description} {repro} {comments}"
                )
                summary_notes_ref += f"  - {title} | {summary} \n"
                summary = f" - {summary}"
            else:
                summary = ""

            with open(file_md, "a", encoding="utf-8") as file:
                file.write(f"- [#{id}]({url}) **{title.strip()}**{summary}\n")


async def finaliseNotes(
    html: bool,
    summary_notes: str,
    file_md: Path,
    file_html: Path,
    section_headers: List[str],
) -> None:
    """
    Finalizes the release notes by adding the summary and table of contents.

    Args:
        html (bool): A boolean flag indicating whether to generate HTML output.
        summary_notes (str): The summary of the work items completed in this release.
        file_md (Path): The path to the output Markdown file.
        file_html (Path): The path to the output HTML file.
        section_headers (List[str]): A list of section headers for the table of contents.

    Returns:
        None
    """
    logging.info("Writing final summary and table of contents...")
    final_summary = await summarise(
        f"{SUMMARY_PROMPT}{SOFTWARE_SUMMARY}\nThe following is a summary of the work items completed in this release:\n{summary_notes}\nYour response should be as concise as possible"
    )
    with open(file_md, "r", encoding="utf-8") as file:
        file_contents = file.read()

    file_contents = file_contents.replace("<NOTESSUMMARY>", final_summary)
    toc = createContents(section_headers)
    file_contents = file_contents.replace("<TABLEOFCONTENTS>", toc)
    file_contents = file_contents.replace(" - .", " - Addressed.")

    if html:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.github.com/markdown",
                json={"text": file_contents},
                headers={"Content-Type": "application/json"},
            ) as markdown_response:
                markdown_text = await markdown_response.text()
                with open(file_html, "w", encoding="utf-8") as file:
                    file.write(markdown_text)

    with open(file_md, "w", encoding="utf-8") as file:
        file.write(file_contents)
