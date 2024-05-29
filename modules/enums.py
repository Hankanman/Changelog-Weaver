# enums.py
from enum import Enum
from modules.config import DEVOPS_API_VERSION


class WorkItemType(Enum):
    EPIC = "Epic"
    FEATURE = "Feature"
    OTHER = "Other"


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class WorkItemField(Enum):
    TITLE = "System.Title"
    DESCRIPTION = "System.Description"
    REPRO_STEPS = "Microsoft.VSTS.TCM.ReproSteps"
    COMMENTS = "System.Comments"
    PARENT = "System.Parent"
    WORK_ITEM_TYPE = "System.WorkItemType"


class ResponseStatus(Enum):
    SUCCESS = 200
    RATE_LIMIT = 429
    ERROR = 500
    NOT_FOUND = 404


class OutputFormat(Enum):
    MARKDOWN = "md"
    HTML = "html"


class APIEndpoint(Enum):
    WORK_ITEM_TYPES = (
        "/{org_name}/{project_name}/_apis/wit/workitemtypes?api-version="
        + DEVOPS_API_VERSION
    )
    WIQL = (
        "/{org_name}/{project_name}/_apis/wit/wiql/{query_id}?api-version="
        + DEVOPS_API_VERSION
    )
    WORK_ITEMS = (
        "/{org_name}/{project_name}/_apis/wit/workitems?ids={ids}&$expand=all&api-version="
        + DEVOPS_API_VERSION
    )
    WORK_ITEM = (
        "/{org_name}/{project_name}/_apis/wit/workitems/{parent_id}?api-version="
        + DEVOPS_API_VERSION
    )
    COMPLETIONS = "/chat/completions"
