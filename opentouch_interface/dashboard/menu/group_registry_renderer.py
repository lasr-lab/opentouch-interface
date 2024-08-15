import streamlit as st

from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry


class GroupRegistryRenderer:
    """ Responsible for rendering all groups registered in the group registry """

    def __init__(self):
        self.group_registry: GroupRegistry = st.session_state.group_registry

    def render(self) -> None:
        self.group_registry = st.session_state.group_registry

        for group in self.group_registry.groups:
            group.render_static()

        # For each group, keep rendering all their member's data
        while True:
            for group in self.group_registry.groups:
                group.render_dynamic()
