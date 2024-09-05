import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.util.util import get_clean_rendering_container
from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry


class GroupRegistryRenderer:
    """ Responsible for rendering all groups registered in the group registry """

    def __init__(self):
        self.group_registry: GroupRegistry = st.session_state.group_registry

    def render(self) -> None:
        self.group_registry = st.session_state.group_registry

        self.group_registry.remove_hidden_groups()

        clean_container: DeltaGenerator = get_clean_rendering_container().container()

        for group in self.group_registry.groups:
            group.render_static(clean_container=clean_container)

        # For each group, keep rendering all their member's data
        while len(st.session_state.group_registry.groups) != 0:
            for group in self.group_registry.groups:
                group.render_dynamic()
