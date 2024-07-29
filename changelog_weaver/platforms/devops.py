"""This module contains the DevOps configuration and API interaction classes."""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import (
    Wiql,
    WorkItemType as AzureWorkItemType,
)

from azure.devops.v7_1.core.models import TeamProjectReference
from msrest.authentication import BasicAuthentication

from ..utilities.utils import format_date, clean_name, clean_string

from ..typings import WorkItem, WorkItemType

FIELDS = [
    "System.Title",
    "System.Id",
    "System.State",
    "System.Tags",
    "System.Description",
    "System.Parent",
    "System.CommentCount",
    "System.WorkItemType",
    "Microsoft.VSTS.Common.Priority",
    "Microsoft.VSTS.TCM.ReproSteps",
    "Microsoft.VSTS.Common.AcceptanceCriteria",
    "Microsoft.VSTS.Scheduling.StoryPoints",
]


@dataclass
class DevOpsConfig:
    """This class holds the configuration for the Azure DevOps API and creates the connection."""

    url: str
    org: str
    project: str
    query: str
    pat: str
    fields: List[str] = field(default_factory=lambda: FIELDS)
    connection: Connection = field(init=False)

    def __post_init__(self):
        credentials = BasicAuthentication("", self.pat)
        self.connection = Connection(
            base_url=f"{self.url}/{self.org}", creds=credentials
        )


class DevOpsClient:
    """This class provides methods to interact with Azure DevOps API."""

    def __init__(self, config: DevOpsConfig):
        self.config = config
        self.connection = config.connection
        self.wit_client = self.connection.clients.get_work_item_tracking_client()
        self.core_client = self.connection.clients.get_core_client()
        self.work_client = self.connection.clients.get_work_client()
        self.work_item_types: Dict[str, WorkItemType] = {}
        self.root_work_item_type: str = ""

    async def initialize(self):
        """Initialize the client by fetching work item types."""
        await self.fetch_work_item_types()
        await self.determine_root_work_item_type()

    async def fetch_work_item_types(self):
        """Fetch work item types and store them in the client."""
        azure_types = self.wit_client.get_work_item_types(self.config.project)
        self.work_item_types = {
            azure_type.name: self._convert_azure_type(azure_type)
            for azure_type in azure_types
        }
        self.work_item_types["Other"] = WorkItemType(
            name="Other",
            icon="https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2",
            color="#333333",
        )

    def _convert_azure_type(self, azure_type: AzureWorkItemType) -> WorkItemType:
        """Convert an Azure DevOps WorkItemType to our WorkItemType model."""
        return WorkItemType(
            name=azure_type.name or "",
            icon=azure_type.icon.url if azure_type.icon else "",
            color=f"#{azure_type.color}" if azure_type.color else "#000000",
        )

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        return self.work_item_types.get(type_name)

    async def determine_root_work_item_type(self):
        """Determine the root work item type based on the backlog configuration."""
        try:
            # Get the project
            project: TeamProjectReference = self.core_client.get_project(
                self.config.project
            )

            # Get the process
            process = self.work_client.get_process_configuration(project.id)

            # Get the portfolio backlogs
            portfolio_backlogs = process.portfolio_backlogs

            if portfolio_backlogs:
                # The first portfolio backlog is typically the highest level (e.g., Epic)
                root_backlog = portfolio_backlogs[0]
                self.root_work_item_type = root_backlog.work_item_types[0].name
            else:
                # If there are no portfolio backlogs, use the requirement backlog
                requirement_backlog = process.requirement_backlog
                self.root_work_item_type = requirement_backlog.work_item_types[0].name

            print(f"Root work item type: {self.root_work_item_type}")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error determining root work item type: {str(e)}")

    def get_all_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        return list(self.work_item_types.values())

    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        """Retrieve work item IDs from a query."""
        query_result = self.wit_client.query_by_id(query_id)
        work_item_ids = [int(row.id) for row in query_result.work_items]
        work_items = self.wit_client.get_work_items(work_item_ids, expand="All")

        return [self._convert_to_work_item(item) for item in work_items]

    async def get_query_wiql(self, query_id: str) -> str:
        """Retrieve the WIQL for a given query."""
        query = self.wit_client.get_query(self.config.project, query_id)
        return query.wiql

    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        """Retrieve details for a specific work item."""
        work_item = self.wit_client.get_work_item(item_id, expand="All")
        return self._convert_to_work_item(work_item)

    async def get_work_items_from_wiql(self, wiql: str) -> List[WorkItem]:
        """Retrieve work items with details using a WIQL query."""
        wiql_object = Wiql(query=wiql)
        query_result = self.wit_client.query_by_wiql(wiql_object).work_items

        work_item_ids = [int(item.id) for item in query_result]
        work_items = self.wit_client.get_work_items(work_item_ids, expand="All")

        return [self._convert_to_work_item(item) for item in work_items]

    def _convert_to_work_item(self, azure_work_item) -> WorkItem:
        """Convert Azure DevOps work item to our WorkItem type."""
        fields = azure_work_item.fields
        work_item_type = fields.get("System.WorkItemType", "")
        work_item_type_info = self.get_work_item_type(work_item_type)

        work_item = WorkItem(
            type=work_item_type,
            root=work_item_type == self.root_work_item_type,
            orphan=fields.get("System.Parent") is None
            and work_item_type != self.root_work_item_type,
            id=azure_work_item.id,
            parent_id=fields.get("System.Parent", 0),
            state=fields["System.State"],
            title=clean_string(fields["System.Title"], min_length=1),
            icon=work_item_type_info.icon if work_item_type_info else "",
            comment_count=fields.get("System.CommentCount", 0),
            story_points=fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
            priority=fields.get("Microsoft.VSTS.Common.Priority"),
            description=clean_string(fields.get("System.Description", ""), 10),
            repro_steps=clean_string(
                fields.get("Microsoft.VSTS.TCM.ReproSteps", ""), 10
            ),
            acceptance_criteria=clean_string(
                fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""), 10
            ),
            tags=(
                fields.get("System.Tags", "").split(";")
                if fields.get("System.Tags")
                else []
            ),
            url=re.sub(
                r"_apis/wit/workitems",
                "_workitems/edit",
                azure_work_item.url,
                flags=re.IGNORECASE,
            ),
            comments=self._get_comments(azure_work_item.id),
        )
        return work_item

    def _get_comments(self, work_item_id: int) -> List[str]:
        """Retrieve comments for a work item."""
        comments = self.wit_client.get_comments(self.config.project, work_item_id)
        return [
            f"{format_date(comment.created_date)} | {clean_name(comment.created_by.display_name)} | {clean_string(comment.text, 10)}"
            for comment in comments.comments
        ]
