from typing import List

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.util.util import get_clean_rendering_container
from opentouch_interface.dashboard.viewers.image.baes_image_viewer import BaseImageViewer
from opentouch_interface.dashboard.viewers.viewer_group import ViewerGroup


class GroupRegistry:
    """
    Manages a collection of ViewerGroups, providing methods to add, remove, and interact with groups.

    The GroupRegistry keeps track of all active ViewerGroups and their associated viewers. It assigns unique
    group indices, facilitates the retrieval of all viewers, and removes groups marked as hidden.
    """

    def __init__(self):
        """
        Initializes an empty GroupRegistry.
        """
        self.groups: List[ViewerGroup] = []
        self._running_group_count: int = 0

    def add_group(self, group: ViewerGroup) -> None:
        """
        Adds a new ViewerGroup to the registry and assigns it a unique group index.

        :param group: The ViewerGroup instance to add.
        """
        group.group_index = self._running_group_count + 1
        self._running_group_count += 1
        self.groups.append(group)

    @property
    def group_count(self) -> int:
        """
        Returns the current number of registered groups.

        :return: Number of registered groups.
        :rtype: int
        """
        return len(self.groups)

    def viewer_count(self) -> int:
        """
        Returns the total number of viewers across all registered groups.

        :return: Total number of viewers in all groups.
        :rtype: int
        """
        return sum(group.viewer_count() for group in self.groups)

    def get_all_viewers(self) -> List[BaseImageViewer]:
        """
        Returns a list of all viewers in all registered groups.

        :return: A list of all viewers.
        :rtype: List[BaseImageViewer]
        """
        viewers: List[BaseImageViewer] = []
        for group in self.groups:
            viewers.extend(group.viewers)
        return viewers

    def remove_hidden_groups(self) -> None:
        """
        Removes all groups that are marked as hidden from the registry.
        """
        self.groups = [group for group in self.groups if not group.hidden]


class GroupRegistryRenderer:
    """
    Handles the rendering of ViewerGroups stored in the GroupRegistry using Streamlit.

    This class is responsible for both static and dynamic rendering of the groups, ensuring that UI elements
    are updated and displayed correctly.
    """

    def __init__(self):
        """
        Initializes the GroupRegistryRenderer and sets up the GroupRegistry from the Streamlit session state.
        """
        self.group_registry: GroupRegistry = st.session_state.group_registry

    def render(self) -> None:
        """
        Renders all registered groups and their viewers. Handles both static content (settings, controls)
        and dynamic content (live data).

        This method removes any hidden groups from the registry before rendering, and it repeatedly
        updates the dynamic content of all visible groups.

        :raises AttributeError: If the `group_registry` is not found in the Streamlit session state.
        """
        # Ensure the latest state of the group registry
        self.group_registry = st.session_state.group_registry

        # Remove hidden groups before rendering
        self.group_registry.remove_hidden_groups()

        # Get a fresh container for rendering
        clean_container: DeltaGenerator = get_clean_rendering_container().container()

        # Render static UI for each group
        for group in self.group_registry.groups:
            group.render_static(clean_container=clean_container)

        # Continuously render dynamic content for each group
        while len(self.group_registry.groups) > 0:
            for group in self.group_registry.groups:
                group.render_dynamic()
