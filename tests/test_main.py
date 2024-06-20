""" Tests for main.py """

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import aiohttp
from src.main import (
    main,
    iterate_and_print,
    write_type_header,
    write_parent_header,
    write_child_item,
)
from src.config import Config
from src.work_items import WorkItems, WorkItemChildren, WorkItem


@pytest.mark.asyncio
async def test_main():
    """Test main function"""
    config = MagicMock(spec=Config)
    session = aiohttp.ClientSession()
    config.session = session

    wi_mock = AsyncMock(spec=WorkItems)
    wi_mock.get_items.return_value = []
    wi_mock.by_type = []

    with patch("main.Config", return_value=config), patch(
        "main.WorkItems", return_value=wi_mock
    ):
        await main()

    wi_mock.get_items.assert_called_once_with(config, session)
    await session.close()


def test_iterate_and_print():
    """Test iterate_and_print function"""
    config = MagicMock(spec=Config)
    session = MagicMock(spec=aiohttp.ClientSession)
    items_by_type = [
        WorkItemChildren(
            type="Bug",
            icon="",
            items=[
                WorkItem(
                    id=1,
                    type="Bug",
                    state="New",
                    title="Test Bug",
                    parent=0,
                    commentCount=0,
                    description="",
                    reproSteps="",
                    acceptanceCriteria="",
                    tags=[],
                    url="",
                    comments=[],
                    icon="",
                    children=[],
                    children_by_type=[],
                )
            ],
        )
    ]

    iterate_and_print(items_by_type, config, session)
    assert config.output.write.call_count == 1


def test_write_type_header():
    """Test write_type_header function"""
    item = WorkItemChildren(type="Bug", icon="icon_url", items=[])
    config = MagicMock(spec=Config)
    write_type_header(item, config, 1, 20)
    config.output.write.assert_called_once_with(
        "# <img src='icon_url' alt='Bug' width='20' height='20'> Bugs\n\n"
    )


def test_write_parent_header():
    """Test write_parent_header function"""
    item = WorkItem(
        id=1,
        type="Bug",
        state="New",
        title="Test Bug",
        parent=0,
        commentCount=0,
        description="",
        reproSteps="",
        acceptanceCriteria="",
        tags=[],
        url="url",
        comments=[],
        icon="icon_url",
        children=[],
        children_by_type=[],
    )
    config = MagicMock(spec=Config)
    write_parent_header(item, config, 1, 20)
    config.output.write.assert_called_once_with(
        "# <img src='icon_url' alt='Bug' width='20' height='20' parent='0'> [#1](url) Test Bug\n\n"
    )


def test_write_child_item():
    """Test write_child_item function"""
    item = WorkItem(
        id=1,
        type="Bug",
        state="New",
        title="Test Bug",
        parent=0,
        commentCount=0,
        description="Test description",
        reproSteps="",
        acceptanceCriteria="",
        tags=[],
        url="url",
        comments=[],
        icon="",
        children=[],
        children_by_type=[],
    )
    config = MagicMock(spec=Config)
    write_child_item(item, config)
    config.output.write.assert_called_once_with(
        "- [#1](url) **Test Bug** Test description 0\n"
    )
