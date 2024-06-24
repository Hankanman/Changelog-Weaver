"""Init for Tests"""

from src.work_items import WorkItem, WorkItemType

TYPE_DATA = [
    {
        "name": "Task",
        "icon": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_clipboard?color=F2CB1D&v=2",
        "color": "#F2CB1D",
    },
    {
        "name": "Bug",
        "icon": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2",
        "color": "#CC293D",
    },
    {
        "name": "Epic",
        "icon": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_crown?color=E06C00&v=2",
        "color": "#E06C00",
    },
    {
        "name": "Feature",
        "icon": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2",
        "color": "#773B93",
    },
    {
        "name": "Product Backlog Item",
        "icon": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_list?color=009CCC&v=2",
        "color": "#009CCC",
    },
    {
        "name": "User Stories",
        "icon": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=ec008c&v=2",
        "color": "#ec008c",
    },
]

TYPES = [WorkItemType(**item) for item in TYPE_DATA]


WORK_ITEM = WorkItem(
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
