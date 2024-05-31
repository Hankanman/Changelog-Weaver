""" This module contains all the enums used in the application. """

from enum import Enum
from .config import DEVOPS_API_VERSION


class WorkItemType(Enum):
    """
    Represents the type of work item.
    """

    EPIC = "Epic"
    FEATURE = "Feature"
    OTHER = "Other"


class LogLevel(Enum):
    """
    Enumeration representing different log levels.

    Attributes:
        INFO (str): Represents the INFO log level.
        WARNING (str): Represents the WARNING log level.
        ERROR (str): Represents the ERROR log level.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class WorkItemField(Enum):
    """
    Enum representing the different fields of a work item.
    """

    TITLE = "System.Title"
    DESCRIPTION = "System.Description"
    REPRO_STEPS = "Microsoft.VSTS.TCM.ReproSteps"
    COMMENTS = "System.Comments"
    PARENT = "System.Parent"
    WORK_ITEM_TYPE = "System.WorkItemType"


class ResponseStatus(Enum):
    """
    Enum class representing the response status codes.

    Attributes:
        SUCCESS (int): Represents a successful response (status code 200).
        RATE_LIMIT (int): Represents a rate limit response (status code 429).
        ERROR (int): Represents an error response (status code 500).
        NOT_FOUND (int): Represents a not found response (status code 404).
        NOT_AUTHORIZED (int): Represents a not authorized response (status code 401).
        FORBIDDEN (int): Represents a forbidden response (status code 403).
    """

    SUCCESS = 200
    RATE_LIMIT = 429
    ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORIZED = 401
    FORBIDDEN = 403


class OutputFormat(Enum):
    """
    Represents the available output formats for generating release notes.
    """

    MARKDOWN = "md"
    HTML = "html"
    PDF = "pdf"


class APIEndpoint(Enum):
    """
    Enum class representing different API endpoints.
    """

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
