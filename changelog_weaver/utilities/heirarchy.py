""" Module for handling the hierarchy of work items. """

from typing import Dict, List, Set
import logging as log

from dataclasses import dataclass
from ..typings import HierarchicalWorkItem, WorkItemGroup


@dataclass
class Hierarchy:
    """Represents the hierarchy of work items."""

    def __init__(self, all_items: Dict[int, HierarchicalWorkItem]) -> None:
        self.all: Dict[int, HierarchicalWorkItem] = all_items
        self.root_items: List[HierarchicalWorkItem] = []
        self.by_type: List[WorkItemGroup] = []
        self._build_hierarchy()

    def _build_hierarchy(self):
        processed_ids: Set[int] = set()

        def process_item(item: HierarchicalWorkItem):
            if item.id in processed_ids:
                return
            processed_ids.add(item.id)

            if item.parent_id and item.parent_id in self.all:
                parent = self.all[item.parent_id]
                if item not in parent.children:
                    parent.children.append(item)
                process_item(parent)
            elif not item.orphan and item.id != 0:
                log.info("Adding root item: %s - %s", item.id, item.title)
                if item not in self.root_items:
                    self.root_items.append(item)

        all_items = list(self.all.values())
        for item in all_items:
            process_item(item)

        # Handle the "Other" parent separately
        other_parent = self.all.get(0)
        if other_parent:
            other_parent.children_by_type = self._group_children_by_type(
                other_parent.children
            )
            self.root_items.append(other_parent)

        # Group children by type for root items (except "Other")
        for item in self.root_items:
            if item.id != 0:  # Skip "Other" parent
                item.children_by_type = self._group_children_by_type(item.children)

        self.by_type = self._group_by_type(self.root_items)

    def _group_children_by_type(
        self, children: List[HierarchicalWorkItem]
    ) -> List[WorkItemGroup]:
        """Group children by their type."""
        type_groups: Dict[str, WorkItemGroup] = {}
        for child in children:
            if child.type not in type_groups:
                type_groups[child.type] = WorkItemGroup(
                    type=child.type, icon=child.icon, items=[]
                )
            type_groups[child.type].items.append(child)
        return list(type_groups.values())

    def _group_by_type(self, items: List[HierarchicalWorkItem]) -> List[WorkItemGroup]:
        """Group work items by their type while preserving hierarchy."""
        grouped_items: Dict[str, List[HierarchicalWorkItem]] = {}
        for item in items:
            if item.type not in grouped_items:
                grouped_items[item.type] = []
            grouped_items[item.type].append(item)

        grouped_children_list = []
        for key, value in grouped_items.items():
            grouped_children_list.append(
                WorkItemGroup(type=key, icon=value[0].icon, items=value)
            )

        # Ensure "Other" is always at the end
        other_items = [item for item in grouped_children_list if item.type == "Other"]
        non_other_items = [
            item for item in grouped_children_list if item.type != "Other"
        ]
        grouped_children_list = non_other_items + other_items

        return grouped_children_list
