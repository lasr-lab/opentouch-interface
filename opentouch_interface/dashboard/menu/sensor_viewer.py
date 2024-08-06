from typing import List

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.menu.util import get_clean_rendering_container
from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer


class SensorViewer:
    def __init__(self):
        if 'viewers' not in st.session_state:
            st.session_state.viewers = []

        self.viewers: List[BaseImageViewer] = st.session_state.viewers
        self.group_key: str = "shown_group"
        self.group: str = 'all'

        if 'recording_state' not in st.session_state:
            st.session_state.recording_state = False

    def _update_viewers(self):
        self.viewers = st.session_state.viewers

    def render_settings(self):
        self._update_viewers()
        dg: DeltaGenerator = get_clean_rendering_container()

        for viewer in self.viewers:
            viewer.update_delta_generator(dg=dg)
            viewer.render_options()

    def render_data(self):
        while True:
            for viewer in self.viewers:
                viewer.render_frame()

    def render_payload(self):
        for viewer in self.viewers:
            viewer.render_payload()

    def select_group(self):
        left, middle, right = st.columns(spec=[0.3, 0.4, 0.3])
        with left:
            self.group = st.selectbox(
                label="Select a group",
                options=self._get_groups(),
                key=self.group_key,
                label_visibility="collapsed"
            )

        with middle:
            path = st.text_input(
                    label="Enter a file path",
                    value=None,
                    placeholder="File name (must have .h5 extension)",
                    label_visibility="collapsed"
                )

        with right:
            st.button(
                label="Stop recording" if st.session_state['recording_state'] else "Start recording",
                type="primary",
                disabled=False,
                use_container_width=True,
                on_click=self.recording,
                args=()
            )

    @staticmethod
    def _get_groups():
        if 'viewers' not in st.session_state:
            return ['all']
        return list({'all'} | {viewer.group for viewer in st.session_state.viewers})

    def recording(self):
        if self.group == 'all':
            viewers: list[BaseImageViewer] = st.session_state.viewers
        else:
            viewers: list[BaseImageViewer] = [v for v in st.session_state.viewers if v.group == self.group]

        for viewer in viewers:
            if st.session_state['recording_state']:
                viewer.sensor.stop_recording()
                viewer.persist_payload()

            else:
                viewer.sensor.start_recording()
        st.session_state['recording_state'] = not st.session_state['recording_state']
