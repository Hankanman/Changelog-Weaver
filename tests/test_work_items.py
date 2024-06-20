""" Tests for work_items module"""

from unittest.mock import MagicMock
import pytest
import aiohttp
from src.work_items import (
    WorkItems,
    WorkItem,
    Types,
)
from src.config import Config


@pytest.mark.asyncio
async def test_work_items_get_items():
    """Test get_items function"""
    config = MagicMock(spec=Config)
    session = aiohttp.ClientSession()
    config.session = session
    wi = WorkItems()

    await wi.get_items(config, session)
    assert not wi.all


@pytest.mark.asyncio
async def test_work_items_fetch_item():
    """Test get_item"""
    config = MagicMock(spec=Config)
    session = aiohttp.ClientSession()
    config.session = session
    wi = WorkItems()

    wi.add_work_item(
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
    )
    item = await wi.fetch_item(config, 1, Types(), session)
    assert item.id == 1


def test_work_items_add_work_item():
    """Test add_work_item function"""
    wi = WorkItems()
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
        url="",
        comments=[],
        icon="",
        children=[],
        children_by_type=[],
    )
    wi.add_work_item(item)
    assert item in wi.all


def test_work_items_group_by_type():
    """Test group_by_type function"""
    wi = WorkItems()
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
        url="",
        comments=[],
        icon="",
        children=[],
        children_by_type=[],
    )
    wi.add_work_item(item)
    grouped = wi.group_by_type([item])
    assert len(grouped) == 1
    assert grouped[0].type == "Bug"
