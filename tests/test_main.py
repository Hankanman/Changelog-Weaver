""" Test the main module. """

from unittest.mock import AsyncMock, MagicMock
import aiohttp
from main import (
    iterate_and_print,
    write_type_header,
    write_parent_header,
    write_child_item,
)
from src.work_items import WorkItem
from src._types import WorkItemChildren
from tests import WORK_ITEM


def mock_config():
    """Mock the config object."""
    config = MagicMock()
    config.session = AsyncMock(spec=aiohttp.ClientSession)
    config.output = MagicMock().a
    return config


def test_iterate_and_print():
    """Test iterate_and_print function."""
    config = mock_config()
    items_by_type = [
        WorkItemChildren(
            type="Bug",
            icon="",
            items=[WORK_ITEM],
        )
    ]

    iterate_and_print(items_by_type, config)
    config.output.write.assert_called()


def test_write_type_header():
    """Test write_type_header function."""
    item = WorkItemChildren(type="Bug", icon="icon_url", items=[WORK_ITEM])
    config = mock_config()
    write_type_header(item, config, 1, 20)
    config.output.write.assert_called_once_with(
        "# <img src='icon_url' height='20'> Bugs\n\n"
    )


def test_write_parent_header():
    """Test write_parent_header function."""
    item = WORK_ITEM
    config = mock_config()
    write_parent_header(item, config, 1, 20)
    config.output.write.assert_called_once_with(
        "# <img src='icon_url' height='20' parent='0'> [#1](url) Test Bug\n\n"
    )


def test_write_child_item():
    """Test write_child_item function."""
    item = WorkItem(
        id=1,
        type="Bug",
        state="New",
        title="Test Bug",
        parent=0,
        comment_count=0,
        description="Test description",
        repro_steps="",
        acceptance_criteria="",
        tags=[],
        url="url",
        comments=[],
        icon="",
        children=[],
        children_by_type=[],
    )
    config = mock_config()
    write_child_item(item, config, 1)
    config.output.write.assert_called_once_with(
        "- [#1](url) **Test Bug** Test description 0\n"
    )
