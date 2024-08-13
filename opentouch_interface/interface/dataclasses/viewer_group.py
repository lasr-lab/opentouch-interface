import os
import random
from typing import List, Dict, Any, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.dataclasses.image.Image_writer import ImageWriter
from opentouch_interface.interface.touch_sensor import TouchSensor


class ViewerGroup:
    def __init__(self, group_name: str, path: Optional[str], viewers: List[BaseImageViewer],
                 payload: List[Dict[str, Any]]):
        self.group_name: str = group_name
        self.path: Optional[str] = path
        self.viewers: List[BaseImageViewer] = [] if viewers is None else viewers
        self.payload: List[Dict[str, Any]] = payload

        self.is_recording: bool = False
        self.wrote_recording: bool = False
        self.container: DeltaGenerator = st.container()

    def viewer_count(self) -> int:
        return len(self.viewers)

    def _toggle_recording(self) -> None:
        for viewer in self.viewers:
            if self.is_recording:
                viewer.sensor.stop_recording()

                # Save group name, path and payload to file
                if self.path:   # This check is redundant as _toggle_recording can only be called when the path is valid
                    ImageWriter.write_attr(file_path=self.path, attribute='group_name', value=self.group_name)
                    ImageWriter.write_attr(file_path=self.path, attribute='path', value=self.path)
                    self._persist_payload()

                self.wrote_recording = True

            else:
                viewer.sensor.start_recording()

        self.is_recording = not self.is_recording

    def _update_stuff(self) -> None:
        self.container = st.container()
        self.container.markdown('###### Sensors')
        for viewer in self.viewers:
            viewer.update_container(container=self.container)

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
                    # Saving of payload only allowed when (1) the file exists and (2) it was written
                    disabled=not (self.path and os.path.exists(self.path) and self.wrote_recording),
                    on_click=self._persist_payload,
                )

    def _persist_payload(self) -> None:
        # Update payload
        for element in self.payload:
            key = element["key"]

            if key in st.session_state:
                element["current_value"] = st.session_state[key]

        # Save payload to disk
        ImageWriter.write_attr(file_path=self.path, attribute='path', value=str(self.payload))

    def _render_data(self) -> None:
        for viewer in self.viewers:
            viewer.render_frame()

    def _render_recording_control(self) -> None:
        self.container.markdown('###### Recording')
        with self.container:
            recording_container = self.container.container(border=True)

            with recording_container:

                # Only groups that don't have any file sensors associated with them, should be allowed to record
                if any(viewer.sensor.config.sensor_type == TouchSensor.SensorType.FILE for viewer in self.viewers):
                    st.info(
                        body='Recording is only available for groups that don\'t contain file sensors.',
                        icon='💡'
                    )
                    return

                left: DeltaGenerator
                right: DeltaGenerator
                left, right = st.columns(spec=[0.6, 0.4])

                with left:
                    path: Optional[str] = st.text_input(
                            label="Enter a file path",
                            value=self.path,
                            placeholder="File name (must have .h5 extension)",
                            label_visibility="collapsed",
                            disabled=self.is_recording
                        )

                    # Check if the entered path is valid
                    if path is not None:
                        if os.path.exists(path):
                            st.warning(
                                body=f'The file {path} already exists!',
                                icon='⚠️'
                            )

                        if path != self.path:
                            self.wrote_recording = False

                        # If the path does not already exist, use it as the new path
                        self.path = path
                        print(self.path)

                with right:
                    st.button(
                        label="Stop recording" if self.is_recording else "Start recording",
                        type="primary",
                        # Recording only allowed when (1) file does not exist
                        disabled=not (self.path and not os.path.exists(self.path)),
                        use_container_width=True,
                        on_click=self._toggle_recording,
                        args=()
                    )

    def render_static(self) -> None:
        st.markdown(f'### Group {self.group_name}')

        self._update_stuff()
        self._render_settings()
        self._render_recording_control()
        self._render_payload()

    def render_dynamic(self) -> None:
        self._render_data()
