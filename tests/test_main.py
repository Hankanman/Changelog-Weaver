""" Tests for main.py """

import os
import base64
import random
from unittest.mock import AsyncMock, patch, mock_open
from dotenv import load_dotenv
import pytest
from src.main import (
    get_parent_ids_by_type,
    get_parent_link_icon,
    get_child_items,
    generate_header,
    group_items_by_type,
    write_header,
    process_items,
    ProcessConfig,
    setup_files,
    encode_pat,
    fetch_parent_items,
    group_items,
    add_other_parent,
    write_notes,
    setup_environment,
    fetch_initial_data,
    fetch_and_process_work_items,
)
from src.config import PAT
from src.enums import WorkItemField


@pytest.fixture
def sample_parent_work_items():
    """
    Returns a dictionary of sample parent work items.

    Each work item is represented by a key-value pair, where the key is the work item ID and the value is a dictionary containing the work item fields and links.
    """
    # Sample parent work items with work item ID as key and work item fields as value
    mock_parent_item_types = ["Feature", "Epic"]
    mock_parent_work_items = {}
    for i in range(10):
        mock_parent_item_type = random.choice(mock_parent_item_types)
        mock_parent_work_items[str(i)] = {
            "id": i,
            "fields": {
                WorkItemField.TITLE.value: f"{mock_parent_item_type} {i}",
                WorkItemField.WORK_ITEM_TYPE.value: mock_parent_item_type,
                WorkItemField.PARENT.value: i,
            },
            "_links": {
                "html": {"href": f"http://example.com/{mock_parent_item_type}/{i}"},
                "workItemIcon": {
                    "url": "http://example.com/icon.png",
                },
            },
            "url": f"http://example.com/{i}",
        }
    return mock_parent_work_items


@pytest.fixture
def sample_work_items():
    """Returns a list of sample work items."""
    mock_item_types = ["Bug", "Task", "User Story"]
    mock_work_items = {}
    for i in range(20):
        mock_item_type = random.choice(mock_item_types)
        mock_work_items[str(i)] = {
            "id": i,
            "fields": {
                WorkItemField.TITLE.value: f"{mock_item_type} {i}",
                WorkItemField.WORK_ITEM_TYPE.value: mock_item_type,
                WorkItemField.PARENT.value: random.choice(
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                ),
            },
            "_links": {
                "html": {"href": f"http://example.com/{mock_item_type}/{i}"},
                "workItemIcon": {
                    "url": "http://example.com/icon.png",
                },
            },
            "url": f"http://example.com/{i}",
        }

    return mock_work_items


def test_get_parent_ids_by_type():
    """Test get_parent_ids_by_type function."""
    result = get_parent_ids_by_type(sample_work_items, "Bug")
    assert result == ["1"]


def test_get_parent_link_icon():
    """Test get_parent_link_icon function."""
    parent_work_item = sample_parent_work_items()["1"]
    work_item_type_to_icon = {"Bug": {"iconUrl": "http://example.com/icon.png"}}
    parent_link, parent_icon_url = get_parent_link_icon(
        parent_work_item, work_item_type_to_icon, "Bug"
    )
    assert parent_link == "http://example.com/1"
    assert parent_icon_url == "http://example.com/icon.png"


def test_get_child_items():
    """Test get_child_items function."""
    result = get_child_items(sample_work_items, 1)
    assert len(result) == 1
    assert result[0]["fields"]["System.Title"] == "Bug 1"


def test_generate_header():
    """Test generate_header function."""
    parent_header = generate_header(
        "1", "http://example.com/1", "http://example.com/icon.png", "Bug 1"
    )
    assert "Bug 1" in parent_header
    assert "http://example.com/icon.png" in parent_header


def test_group_items_by_type():
    """Test group_items_by_type function."""
    child_items = sample_work_items
    result = group_items_by_type(child_items)
    assert "Bug" in result
    assert len(result["Bug"]) == 1


@patch("builtins.open", new_callable=mock_open)
def test_write_header(mock_open_instance):
    """Test write_header function."""
    write_header("dummy_file.md", "Parent Header")

    # Check if the file was opened with the correct parameters
    mock_open_instance.assert_called_once_with("dummy_file.md", "a", encoding="utf-8")

    # Get the handle to the file and check if 'write' was called with the correct parameters
    handle = mock_open_instance()
    handle.write.assert_called_once_with("Parent Header")


@pytest.mark.asyncio
async def test_process_items():
    """Test process_items function."""
    session = AsyncMock()
    file_md = "dummy_file.md"
    summarize_items = True
    work_item_type_to_icon = {"Bug": {"iconUrl": "http://example.com/icon.png"}}

    config = ProcessConfig(session, file_md, summarize_items, work_item_type_to_icon)
    summary_notes = await process_items(
        config, sample_work_items, sample_parent_work_items
    )

    assert "- Bug 1\n" in summary_notes


def test_setup_files():
    """Test setup_files function."""
    file_md, file_html = setup_files()
    assert file_md.exists()
    assert file_html.exists()


def test_encode_pat():
    """Test encode_pat function."""
    encoded_pat = encode_pat()
    assert encoded_pat == base64.b64encode(f":{PAT}".encode()).decode()


@pytest.mark.asyncio
async def test_fetch_parent_items():
    """Test fetch_parent_items function."""
    session = AsyncMock()
    session.get = AsyncMock(
        return_value=AsyncMock(
            json=AsyncMock(
                return_value={"id": "1", "fields": {"System.Title": "Bug 1"}}
            )
        )
    )
    parent_ids = ["1"]
    result = await fetch_parent_items(session, "test_org", "test_project", parent_ids)
    assert "1" in result
    assert result["1"]["fields"]["System.Title"] == "Bug 1"


def test_group_items():
    """Test group_items function."""
    result = group_items(sample_work_items)
    assert "1" in result
    assert len(result["1"]) == 1


def test_add_other_parent():
    """Test add_other_parent function."""
    add_other_parent(sample_parent_work_items)
    assert sample_parent_work_items.get("0") is not None


@pytest.mark.asyncio
async def test_write_notes():
    """Test write_notes function."""
    query_id = "test_query"
    section_header = "Resolved Issues"
    summarize_items = True
    output_html = True

    result = await write_notes(query_id, section_header, summarize_items, output_html)
    assert "<NOTESSUMMARY>" not in result
    assert "<TABLEOFCONTENTS>" not in result


def test_setup_environment():
    """Test setup_environment function."""
    org_name_escaped, project_name_escaped, devops_headers = setup_environment()
    assert org_name_escaped == "test_org"
    assert project_name_escaped == "test_project"
    assert (
        devops_headers["Authorization"]
        == f"Basic {base64.b64encode(f':{PAT}'.encode()).decode()}"
    )


@pytest.mark.asyncio
async def test_fetch_initial_data():
    """Test fetch_initial_data function."""
    session = AsyncMock()
    session.get = AsyncMock(
        return_value=AsyncMock(
            json=AsyncMock(
                return_value={
                    "value": [
                        {"name": "Bug", "icon": {"url": "http://example.com/icon.png"}}
                    ]
                }
            )
        )
    )
    work_item_type_to_icon = await fetch_initial_data(session, "test_query")
    assert "Bug" in work_item_type_to_icon


@pytest.mark.asyncio
async def test_fetch_and_process_work_items():
    """Test fetch_and_process_work_items function."""
    session = AsyncMock()
    session.get = AsyncMock(
        return_value=AsyncMock(
            json=AsyncMock(
                return_value={"id": "1", "fields": {"System.Title": "Bug 1"}}
            )
        )
    )
    result = await fetch_and_process_work_items(
        session, "test_org", "test_project", sample_work_items
    )
    assert "1" in result
    assert result["1"]["fields"]["System.Title"] == "Bug 1"


@pytest.fixture(scope="module", autouse=True)
def load_test_env():
    """Load environment variables from .env.test file."""
    load_dotenv(dotenv_path=".env.test")


def test_env_variables():
    """Test environment variables."""
    assert os.getenv("PAT") == "test_pat_value"
    assert os.getenv("GPT_API_KEY") == "test_gpt_api_key_value"
