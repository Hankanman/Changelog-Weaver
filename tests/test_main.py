""" Tests for main.py """

import re
import random
from pathlib import Path
from unittest.mock import AsyncMock, patch, mock_open, MagicMock
from datetime import datetime, timedelta
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
)
from src.enums import WorkItemField, WorkItemType, WorkItemState


class MockResponse:
    """A mock response class for the aiohttp.ClientSession.get method."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        """Returns a list of sample work items."""
        return sample_work_items

@pytest.fixture
def mock_model_config():
    """Returns a mock ModelConfig object."""
    mock_config = MagicMock()
    mock_config.gpt_api_key = 'mock_api_key'
    mock_config.gpt_base_url = 'http://example.com'
    mock_config.model = 'mock_model'
    mock_config.models = [{'Name': 'mock_model', 'Tokens': 8192}]
    return mock_config

@pytest.fixture
def sample_parent_work_items():
    """
    Returns a dictionary of sample parent work items.

    Each work item is represented by a key-value pair, where the key is the work item ID and the value is a dictionary containing the work item fields and links.
    """
    # Sample parent work items with work item ID as key and work item fields as value
    mock_parent_item_types = [
        WorkItemType.EPIC.value,
        WorkItemType.FEATURE.value,
        WorkItemType.OTHER.value,
    ]
    mock_parent_work_items = []
    for i in range(10):
        mock_parent_item_type = random.choice(mock_parent_item_types)
        mock_parent_work_items.append(
            {
                "name": f"{mock_parent_item_type} {i}",
                "icon": {"url": "http://example.com/icon.png"},
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
        )
    return mock_parent_work_items


@pytest.fixture
def sample_work_items():
    """Returns a list of sample work items."""
    mock_item_types = [
        WorkItemType.BUG.value,
        WorkItemType.USER_STORY.value,
        WorkItemType.TASK.value,
        WorkItemType.PRODUCT_BACKLOG_ITEM.value,
    ]
    mock_work_items = []
    for i in range(20):
        mock_item_type = random.choice(mock_item_types)
        mock_work_items.append(
            {
                "name": f"{mock_item_type} {i}",
                "icon": {"url": "http://example.com/icon.png"},
                "id": i,
                "fields": {
                    WorkItemField.TITLE.value: f"{mock_item_type} {i}",
                    WorkItemField.WORK_ITEM_TYPE.value: mock_item_type,
                    WorkItemField.PARENT.value: random.choice(
                        [None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    ),
                    WorkItemField.AREA_PATH.value: "Sample Area Path",
                    WorkItemField.TEAM_PROJECT.value: "Sample Team Project",
                    WorkItemField.STATE.value: random.choice(list(WorkItemState)).value,
                    WorkItemField.REASON.value: "Sample Reason",
                    WorkItemField.ASSIGNED_TO.value: "Sample User",
                    WorkItemField.CREATED_DATE.value: (
                        datetime.now() - timedelta(days=random.randint(1, 30))
                    ).isoformat(),
                    WorkItemField.CREATED_BY.value: "Sample Creator",
                    WorkItemField.CHANGED_DATE.value: datetime.now().isoformat(),
                    WorkItemField.CHANGED_BY.value: "Sample Changer",
                    WorkItemField.PRIORITY.value: random.randint(1, 4),
                    WorkItemField.SEVERITY.value: random.choice(
                        ["1 - Critical", "2 - High", "3 - Medium", "4 - Low"]
                    ),
                    WorkItemField.VALUE_AREA.value: "Business",
                    WorkItemField.ITERATION_PATH.value: "Sample Iteration Path",
                    WorkItemField.TAGS.value: "Sample Tag",
                },
                "_links": {
                    "html": {"href": f"http://example.com/{mock_item_type}/{i}"},
                    "workItemIcon": {"url": "http://example.com/icon.png"},
                },
                "url": f"http://example.com/{i}",
            }
        )

    return mock_work_items


# pylint: disable=redefined-outer-name
def test_get_parent_ids_by_type(sample_work_items):
    """Test get_parent_ids_by_type function."""
    result = get_parent_ids_by_type(sample_work_items, "Feature")
    assert isinstance(result, list)
    for item in result:
        assert (
            sample_work_items[str(item)]["fields"]["System.WorkItemType"] == "Feature"
        )


# pylint: disable=redefined-outer-name
def test_get_parent_link_icon(sample_parent_work_items):
    """Test get_parent_link_icon function."""
    parent_work_item = sample_parent_work_items[1]
    work_item_type_to_icon = {"Bug": {"iconUrl": "http://example.com/icon.png"}}
    parent_link, parent_icon_url = get_parent_link_icon(
        parent_work_item, work_item_type_to_icon, "Bug"
    )
    pattern = rf"http://example\.com/({WorkItemType.EPIC.value}|{WorkItemType.FEATURE.value}|{WorkItemType.OTHER.value})/\d+$"
    assert re.match(pattern, parent_link)
    assert parent_icon_url == "http://example.com/icon.png"


# pylint: disable=redefined-outer-name
def test_get_child_items(sample_work_items):
    """Test get_child_items function."""
    result = get_child_items(sample_work_items, 1)
    pattern = rf"(({WorkItemType.BUG.value}|{WorkItemType.USER_STORY.value}|{WorkItemType.TASK.value}|{WorkItemType.PRODUCT_BACKLOG_ITEM.value}) \d+)$"
    assert len(result) >= 1
    match = re.fullmatch(pattern, result[0]["fields"]["System.Title"])
    assert (
        match is not None
    ), f'"{result[0]["fields"]["System.Title"]}" does not match pattern "{pattern}"'


def test_generate_header():
    """Test generate_header function."""
    parent_header = generate_header(
        1, "http://example.com/1", "http://example.com/icon.png", "Bug 1"
    )
    assert "Bug 1" in parent_header
    assert "http://example.com/icon.png" in parent_header


def test_group_items_by_type(sample_work_items):
    """Test group_items_by_type function."""
    result = group_items_by_type(sample_work_items)
    assert "Bug" in result
    assert len(result["Bug"]) >= 1


@patch("builtins.open", new_callable=mock_open)
def test_write_header(mock_open_instance):
    """Test write_header function."""
    write_header("dummy_file.md", "Parent Header")

    # Check if the file was opened with the correct parameters
    mock_open_instance.assert_called_once_with("dummy_file.md", "a", encoding="utf-8")

    # Get the handle to the file and check if 'write' was called with the correct parameters
    handle = mock_open_instance()
    handle.write.assert_called_once_with("Parent Header")


# pylint: disable=redefined-outer-name
@pytest.mark.asyncio
@patch('src.config.ModelConfig', autospec=True)
async def test_process_items(sample_work_items, sample_parent_work_items):
    """Test process_items function."""
    session = AsyncMock()
    file_md = "dummy_file.md"
    summarize_items = True
    work_item_type_to_icon = {"Bug": {"iconUrl": "http://example.com/icon.png"}}

    config = ProcessConfig(session, file_md, summarize_items, work_item_type_to_icon)
    summary_notes = await process_items(
        config,
        sample_work_items,
        sample_parent_work_items,
    )

    work_item_types = [
        WorkItemType.BUG.value,
        WorkItemType.USER_STORY.value,
        WorkItemType.TASK.value,
        WorkItemType.PRODUCT_BACKLOG_ITEM.value,
        WorkItemType.EPIC.value,
        WorkItemType.FEATURE.value,
        WorkItemType.OTHER.value,
    ]

    pattern = rf"^(- ({'|'.join(work_item_types)}) \d+)$"
    matches = re.findall(pattern, summary_notes, re.MULTILINE)
    assert len(matches) == len(
        summary_notes.rstrip().split("\n")
    ), f'"{summary_notes}" does not match pattern "{pattern}"'


@patch("src.config.Config")
def test_setup_files(mock_config):
    """Test setup_files function."""
    mock_config.return_value = MagicMock()
    mock_config.return_value.solution_name = "Your Solution Name"
    mock_config.return_value.release_version = f"1.0.{datetime.now().strftime("%Y%m%d")}.1"
    mock_config.return_value.output_folder = Path("Releases")
    mock_config.return_value.software_summary = "mock_summary"

    file_md, file_html = setup_files(mock_config.return_value)

    print(
        f"Expected HTML file location: {mock_config.return_value.output_folder / 'mock_solution-v.html'}"
    )
    print(f"Actual HTML file location: {file_html}")

    assert file_md.exists()
    assert file_html.exists()
