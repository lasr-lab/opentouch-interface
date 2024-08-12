import os
import random
from typing import List, Dict, Any, Optional

import h5py
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer


class ViewerGroup:
    def __init__(self, group_name: str, viewers: List[BaseImageViewer], payload: List[Dict[str, Any]]):
        self.group_name: str = group_name
        self.viewers: List[BaseImageViewer] = [] if viewers is None else viewers
        self.payload: List[Dict[str, Any]] = payload

        self.is_recording: bool = False
        self.container: DeltaGenerator = st.container()
        self.path: Optional[str] = None

    def viewer_count(self) -> int:
        return len(self.viewers)

    def _toggle_recording(self) -> None:
        for viewer in self.viewers:
            if self.is_recording:
                viewer.sensor.stop_recording()
            else:
                viewer.sensor.start_recording()

        self.is_recording = not self.is_recording

    def _update_stuff(self) -> None:
        self.container = st.container()
        self.container.markdown('###### Sensors')
        for viewer in self.viewers:
            viewer.update_delta_generator(dg=self.container)

    def _render_settings(self) -> None:
        for viewer in self.viewers:
            viewer.render_options()

    def _render_payload(self) -> None:
        self.container.markdown('###### Payload')
        if not self.payload:
            return

        with self.container:
            payload_container = self.container.container(border=True)

            with payload_container:
                for element in self.payload:
                    element_type = element['type']

                    if "key" not in element:
                        element["key"] = random.random()

                    if element_type == "slider":
                        st.slider(
                            label=element.get("label", "Some slider input"),
                            min_value=element.get("min_value", 0),
                            max_value=element.get("max_value", 100),
                            value=element.get("default", 0),
                            step=1,
                            label_visibility="visible",
                            key=element["key"],
                        )

                    elif element_type == "text_input":
                        st.text_input(
                            label=element.get("label", "Some text input"),
                            value=element.get("default", ""),
                            label_visibility="visible",
                            key=element["key"],
                        )

                st.button(
                    label="Save changes",
                    type="primary",
                    disabled=not (self.path and os.path.exists(self.path)),
                    on_click=self._persist_payload,
                )

    def _persist_payload(self) -> None:
        # Update payload
        for element in self.payload:
            key = element["key"]

            if key in st.session_state:
                element["current_value"] = st.session_state[key]

        # Save payload to disk
        if os.path.exists(self.path):
            with h5py.File(self.path, 'r+') as hf:
                hf.attrs['payload'] = str(self.payload)

    def _render_data(self) -> None:
        for viewer in self.viewers:
            viewer.render_frame()

    def _render_recording_control(self) -> None:
        self.container.markdown('###### Recording')
        with self.container:
            recording_container = self.container.container(border=True)

            with recording_container:
                left: DeltaGenerator
                right: DeltaGenerator
                left, right = st.columns(spec=[0.6, 0.4])

                with left:
                    path: Optional[str] = st.text_input(
                            label="Enter a file path",
                            value="",
                            placeholder="File name (must have .h5 extension)",
                            label_visibility="collapsed"
                        )
                    if path is not None and not os.path.exists(path):
                        self.path = path

                with right:
                    st.button(
                        label="Stop recording" if self.is_recording else "Start recording",
                        type="primary",
                        disabled=not (self.path and not os.path.exists(self.path)),
                        use_container_width=True,
                        on_click=self._toggle_recording,
                        args=()
                    )

    def render_static(self) -> None:
        st.markdown(f'#### Group {self.group_name}')

        self._update_stuff()
        self._render_settings()
        self._render_payload()
        self._render_recording_control()

    def render_dynamic(self) -> None:
        self._render_data()
