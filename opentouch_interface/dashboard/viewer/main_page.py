import random

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


class MainPage:
    """
    Main page class to handle the rendering of frames and viewers.
    """
    @staticmethod
    def render_frames():
        """
        Render frames for all viewers stored in the session state.
        """
        if 'viewers' in st.session_state:
            for viewer in st.session_state.viewers:
                viewer.render_frame()

    @staticmethod
    def render_viewers():
        """
        Render options for all viewers stored in the session state.
        """
        if 'viewers' in st.session_state:
            for viewer in st.session_state.viewers:
                viewer.render_options()

    def update_renderer(self):
        """
        Update the delta generator for each viewer.
        """
        dg = self.get_clean_rendering_container(app_state=f"{random.random()}")

        if 'viewers' in st.session_state:
            for viewer in st.session_state.viewers:
                viewer.update_delta_generator(dg)

    @staticmethod
    def get_clean_rendering_container(app_state: str) -> DeltaGenerator:
        """
        Ensure a clean rendering container on state changes.
        """
        slot_in_use = st.session_state.slot_in_use = st.session_state.get("slot_in_use", "a")
        if app_state != st.session_state.get("previous_state", app_state):
            if slot_in_use == "a":
                slot_in_use = st.session_state.slot_in_use = "b"
            else:
                slot_in_use = st.session_state.slot_in_use = "a"

        st.session_state.previous_state = app_state

        slot = {
            "a": st.empty(),
            "b": st.empty(),
        }[slot_in_use]

        return slot.container()
