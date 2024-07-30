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
