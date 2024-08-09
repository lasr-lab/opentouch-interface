import streamlit as st

from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry


class GroupRegistryRenderer:
    """ Responsible for rendering all groups registered in the group registry """

    def __init__(self):
        self.group_registry: GroupRegistry = st.session_state.group_registry

    def _render_settings(self) -> None:
        for group in self.group_registry.groups:
            group.render_settings()

    def _render_payload(self) -> None:
        for group in self.group_registry.groups:
            group.render_payload()

    def _render_data(self) -> None:
        for group in self.group_registry.groups:
            group.render_data()

    def _render_recording_control(self) -> None:
        for group in self.group_registry.groups:
            group.render_recording_control()

    def _reload_groups(self) -> None:
        self.group_registry = st.session_state.group_registry

        for group in self.group_registry.groups:
            group.update_stuff()

    def render(self) -> None:
        # Reload all registered groups
        self._reload_groups()

        # Render the recording button, sensor settings and payload for every group
        self._render_settings()
        self._render_recording_control()
        self._render_payload()

        # For each group, keep rendering all their member's data
        while True:
            self._render_data()
