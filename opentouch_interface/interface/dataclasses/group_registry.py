from typing import List

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.dataclasses.viewer_group import ViewerGroup


class GroupRegistry:
    def __init__(self):
        self.groups: List[ViewerGroup] = []
        self._running_group_count: int = 0

    def add_group(self, group: ViewerGroup) -> None:
        # Tell group its index in global GroupRegistry
        group.group_index = self._running_group_count + 1
        self._running_group_count += 1

        self.groups.append(group)

    @property
    def group_count(self) -> int:
        return len(self.groups)

    def viewer_count(self) -> int:
        return sum(viewer.viewer_count() for viewer in self.groups)

    def get_all_viewers(self) -> List[BaseImageViewer]:
        viewers: List[BaseImageViewer] = []
        for group in self.groups:
            viewers.extend(group.viewers)
        return viewers

    def remove_hidden_groups(self):
        for group in self.groups:
            if group.hidden:
                self.groups.remove(group)
