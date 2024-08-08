from typing import List, Dict, Any

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer


class ViewerGroup:
    def __init__(self, group_name: str, viewers: List[BaseImageViewer], payload: List[Dict[str, Any]]):
        self.group_name: str = group_name
        self.viewers: List[BaseImageViewer] = [] if viewers is None else viewers
        self.payload: List[Dict[str, Any]] = payload

    def add_viewer(self, viewer: BaseImageViewer):
        self.viewers.append(viewer)

    def viewer_count(self):
        return len(self.viewers)
