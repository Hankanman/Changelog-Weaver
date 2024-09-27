""" DevOps API module for fetching work items from Azure DevOps """

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
import aiohttp
from azure.devops.v7_1.work_item_tracking.models import (
    Wiql,
    WorkItemType as AzureWorkItemType,
)
from azure.devops.v7_1.core.models import TeamProjectReference
from azure.devops.v7_1.git.models import GitQueryCommitsCriteria
from azure.devops.exceptions import AzureDevOpsServiceError
from ..utilities import format_date, clean_name, clean_string
from ..typings import WorkItem, WorkItemType, CommitInfo
from ..logger import get_logger

log = get_logger(__name__)

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


# pylint: disable=too-many-instance-attributes
class DevOpsAPI:
    """Class for fetching work items from Azure DevOps"""

    def __init__(self, config):
        self.config = config
        self.connection = config.connection
        try:
            self.wit_client = self.connection.clients.get_work_item_tracking_client()
            self.core_client = self.connection.clients.get_core_client()
            self.work_client = self.connection.clients.get_work_client()
            self.git_client = self.connection.clients.get_git_client()
        except AzureDevOpsServiceError as e:
            log.error(f"Error initializing DevOps API: {str(e)}")
        self.work_item_types: Dict[str, WorkItemType] = {}
        self.root_work_item_type: str = ""
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.repo_name = config.repo_name

    async def initialize(self):
        """Initialize the API client"""
        self.session = aiohttp.ClientSession()
        await self.fetch_work_item_types()
        await self.determine_root_work_item_type()

    async def close(self):
        """Close the API client"""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)

    async def fetch_work_item_types(self):
        """Fetch all work item types from the project"""
        loop = asyncio.get_event_loop()
        azure_types = await loop.run_in_executor(
            self.executor, self.wit_client.get_work_item_types, self.config.project
        )
        self.work_item_types = {
            azure_type.name: self._convert_azure_type(azure_type)
            for azure_type in azure_types
        }
        self.work_item_types["Other"] = WorkItemType(
            name="Other",
            icon="https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2",
            color="#333333",
        )

    async def get_commits(self, **kwargs) -> List[CommitInfo]:
        """Fetch commits from the Azure DevOps repository."""
        loop = asyncio.get_event_loop()

        if not self.repo_name:
            log.error("Repository name is not specified in the configuration")
            return []

        try:
            repo = await loop.run_in_executor(
                self.executor,
                lambda: self.git_client.get_repository(
                    self.repo_name, self.config.project
                ),
            )
        except AzureDevOpsServiceError:
            log.error(f"Repository '{self.repo_name}' not found in the project")
            return []

        # Create criteria for querying commits
        criteria = GitQueryCommitsCriteria(
            include_links=False,
            skip=0,
            top=100,  # Adjust this number as needed
        )

        # Add date filters if provided
        if "since" in kwargs:
            criteria.from_date = kwargs["since"]
        if "until" in kwargs:
            criteria.to_date = kwargs["until"]

        commits = await loop.run_in_executor(
            self.executor,
            lambda: self.git_client.get_commits(
                repository_id=repo.id,
                search_criteria=criteria,
                project=self.config.project,
            ),
        )

        return [
            CommitInfo(
                sha=commit.commit_id,
                message=commit.comment,
                author=commit.author.name,
                date=format_date(commit.author.date),
                url=f"{repo.web_url}/commit/{commit.commit_id}",
            )
            for commit in commits
        ]

    def _convert_azure_type(self, azure_type: AzureWorkItemType) -> WorkItemType:
        return WorkItemType(
            name=azure_type.name or "",
            icon=azure_type.icon.url if azure_type.icon else "",
            color=f"#{azure_type.color}" if azure_type.color else "#000000",
        )

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get the work item type by name"""
        return self.work_item_types.get(type_name)

    async def determine_root_work_item_type(self):
        """Determine the root work item type for the project"""
        try:
            loop = asyncio.get_event_loop()
            project: TeamProjectReference = await loop.run_in_executor(
                self.executor, self.core_client.get_project, self.config.project
            )
            process = await loop.run_in_executor(
                self.executor, self.work_client.get_process_configuration, project.id
            )
            portfolio_backlogs = process.portfolio_backlogs

            if portfolio_backlogs:
                root_backlog = portfolio_backlogs[0]
                self.root_work_item_type = root_backlog.work_item_types[0].name
            else:
                requirement_backlog = process.requirement_backlog
                self.root_work_item_type = requirement_backlog.work_item_types[0].name

            log.info(f"Root work item type: {self.root_work_item_type}")
        except aiohttp.ClientError as e:
            log.error(f"Error determining root work item type: {str(e)}")

    def get_all_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types"""
        return list(self.work_item_types.values())

    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        """Get work items from a query"""
        start_time = time.time()
        log.info("Starting to fetch work items from query %s", query_id)

        loop = asyncio.get_event_loop()
        query_result = await loop.run_in_executor(
            self.executor, lambda: self.wit_client.query_by_id(query_id)
        )
        work_item_ids = [int(row.id) for row in query_result.work_items]

        log.info("Found %s work item IDs from query", len(work_item_ids))

        items = await self.get_work_items(work_item_ids)

        end_time = time.time()
        duration = end_time - start_time
        log.info(
            "Finished fetching %s work items in %.2f seconds", len(items), duration
        )

        return items

    async def get_query_wiql(self, query_id: str) -> str:
        """Get the WIQL for a query"""
        loop = asyncio.get_event_loop()
        query = await loop.run_in_executor(
            self.executor, self.wit_client.get_query, self.config.project, query_id
        )
        return query.wiql

    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        """Get a work item by ID"""
        loop = asyncio.get_event_loop()
        azure_work_item = await loop.run_in_executor(
            self.executor, lambda: self.wit_client.get_work_item(item_id, expand="All")
        )
        return await self._convert_to_work_item(azure_work_item)

    async def get_work_items_from_wiql(self, wiql: str) -> List[WorkItem]:
        """Get work items from a WIQL query"""
        loop = asyncio.get_event_loop()
        wiql_object = Wiql(query=wiql)
        query_result = await loop.run_in_executor(
            self.executor, lambda: self.wit_client.query_by_wiql(wiql_object)
        )
        work_item_ids = [int(item.id) for item in query_result.work_items]
        return await self.get_work_items(work_item_ids)

    async def get_work_items(self, work_item_ids: List[int]) -> List[WorkItem]:
        """Get work items by ID"""
        start_time = time.time()
        log.info("Starting to fetch details for %s work items", len(work_item_ids))

        tasks = [self.get_work_item_by_id(item_id) for item_id in work_item_ids]
        items = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time
        log.info(
            "Finished fetching details for %s work items in %.2f seconds",
            len(items),
            duration,
        )

        return items

    async def _convert_to_work_item(self, azure_work_item) -> WorkItem:
        fields = azure_work_item.fields
        work_item_type = fields.get("System.WorkItemType", "")
        work_item_type_info = self.get_work_item_type(work_item_type)

        return WorkItem(
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
            url=azure_work_item.url.lower().replace(
                "_apis/wit/workitems", "_workitems/edit"
            ),
            comments=await self._get_comments(azure_work_item.id),
        )

    async def _get_comments(self, work_item_id: int) -> List[str]:
        loop = asyncio.get_event_loop()
        comments = await loop.run_in_executor(
            self.executor,
            lambda: self.wit_client.get_comments(self.config.project, work_item_id),
        )
        return [
            f"{format_date(comment.created_date)} | {clean_name(comment.created_by.display_name)} | {clean_string(comment.text, 10)}"
            for comment in comments.comments
        ]
