from typing import List

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.dataclasses.viewer_group import ViewerGroup


class GroupRegistry:
    def __init__(self):
        self.groups: List[ViewerGroup] = []

    def add_group(self, group: ViewerGroup) -> None:
        if any(group.group_name == g.group_name for g in self.groups):
            raise ValueError(f"Group with name {group.group_name} already registered")

        self.groups.append(group)

    def group_count(self) -> int:
        return len(self.groups)

    def viewer_count(self) -> int:
        return sum(viewer.viewer_count() for viewer in self.groups)

    def get_all_viewers(self) -> List[BaseImageViewer]:
        viewers: List[BaseImageViewer] = []
        for group in self.groups:
            viewers.extend(group.viewers)
        return viewers
