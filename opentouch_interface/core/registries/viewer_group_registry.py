import time

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.viewers.base_viewer import BaseViewer
from opentouch_interface.dashboard.viewers.viewer_group import ViewerGroup


class ViewerGroupRegistry:
    def __init__(self):
        self.viewer_groups: list[ViewerGroup] = []
        self._running_group_count: int = 0
        self._max_group_count: int = 0

    def add(self, viewer_group: ViewerGroup):
        viewer_group._group_idx = self._running_group_count
        self._running_group_count += 1
        self.viewer_groups.append(viewer_group)
        self._max_group_count = max(self._max_group_count, len(self.viewer_groups))

    def remove_and_unload(self, viewer_group: ViewerGroup):
        # Call disconnect
        viewer_group.hidden = True
        viewer_group.disconnect()

        # Remove hidden viewer groups
        if viewer_group in self.viewer_groups:  # If clicking fast, one can remove a viewer twice in the dashboard
            self.viewer_groups.remove(viewer_group)

    @property
    def group_count(self) -> int:
        return len(self.viewer_groups)

    @property
    def viewer_count(self) -> int:
        return sum(viewer_group.viewer_count for viewer_group in self.viewer_groups)

    @property
    def viewers(self) -> list[BaseViewer]:
        return [viewer for viewer_group in self.viewer_groups for viewer in viewer_group.viewers]

    def render(self) -> None:
        # Get a fresh container for rendering
        # if CentralRegistry.update_container():
        #     clean_container: DeltaGenerator = get_clean_rendering_container().container()
        #     CentralRegistry.update_container(value=False)
        # else:
        #     clean_container: DeltaGenerator = st.container()

        clean_container: DeltaGenerator = st.container()

        # Render static UI for each group
        for viewer_group in self.viewer_groups:
            if not viewer_group.hidden:
                viewer_group.update_container(clean_container)
                viewer_group.render_static()

        # Add an empty element at the bottom to prevent shadow elements
        # (see https://discuss.streamlit.io/t/looking-for-a-proper-way-of-resolving-ghost-shadow-mirage-left-by-widget-
        # after-session-state-change-my-current-workaround-is-hacky/86638)
        for _ in range(self._max_group_count):
            clean_container.empty()

        # Continuously render dynamic content for each group
        while len(self.viewer_groups) > 0:
            start_time = time.time()  # Record the start time of the loop
            for viewer_group in self.viewer_groups:
                viewer_group.render_dynamic()

            # Calculate elapsed time and sleep for the remaining frame duration
            elapsed_time = time.time() - start_time
            frame_duration = 1 / 30  # Desired frame duration for 30 FPS
            sleep_time = max(0.0, frame_duration - elapsed_time)
            time.sleep(float(sleep_time))
