""" This module contains the DevOps class that holds the configuration for the Azure DevOps API. """

import base64
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DevOps:
    """This class holds the configuration for the Azure DevOps API.

    Args:
        url (str): The base URL for the Azure DevOps API.
        api_version (str): The version of the Azure DevOps API.
        org (str): The organization name.
        project (str): The project name.
        query (str): The query to search for work items.
        pat (str): The personal access token.
        fields (Optional[List[str]]): The fields to include in the work item query. If None is provided, the default fields will be used.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        url: str,
        api_version: str,
        org: str,
        project: str,
        query: str,
        pat: str,
        fields: Optional[List[str]] = None,
    ):
        self.url = url
        self.api_version = api_version
        self.org = org
        self.project = project
        self.query = query
        self.pat = base64.b64encode(f":{pat}".encode()).decode()
        if fields:
            self.fields = fields
        else:
            self.fields: List[str] = [
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
