""" This module manages the list of all work item types. """

import logging as log
from typing import List, Optional
from src.config import Config
from src.utils import send_request
from ._types import WorkItemType


class ItemTypes:
    """Manages the list of all work item types."""

    def __init__(self):
        self.all = {}

    async def get(self, config: Config):
        """Create a new instance of Types."""
        self.all = await self.fetch_types(config)
        return self

    async def fetch_types(self, config: Config) -> dict[str, WorkItemType]:
        """Fetch work item types asynchronously."""
        uri = f"{config.devops.url}/{config.devops.org}/{config.devops.project}/_apis/wit/workitemtypes"
        headers = {"Authorization": f"Basic {config.devops.pat}"}
        log.info("Fetching Work Item Types")
        types_data = await send_request(uri, headers=headers)

        types_values = types_data.get("value", [])

        types = {
            type["name"]: WorkItemType(
                name=type["name"],
                icon=type["icon"]["url"],
                color=str.format("#{}", type["color"]),
            )
            for type in types_values
        }
        types = types | {
            "Other": WorkItemType(
                name="Other",
                icon="https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2",
                color="#333333",
            )
        }
        return types

    def get_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        return self.all.get(type_name)

    def get_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        return list(self.all.values())
