import os
from typing import List, Dict, Any, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.dashboard.menu.viewers.image.file_viewer import FileViewer
from opentouch_interface.interface.dataclasses.image.image_writer import ImageWriter


class ViewerGroup:
    def __init__(self, group_name: str, path: Optional[str], viewers: List[BaseImageViewer],
                 payload: List[Dict[str, Any]]):
        self.group_name: str = group_name
        self._path: Optional[str] = path
        self.viewers: List[BaseImageViewer] = viewers or []
        self.payload: List[Dict[str, Any]] = payload

        self.has_file_sensors: bool = any(viewer.sensor.config.sensor_type == 'FILE' for viewer in self.viewers)

        self.is_recording: bool = False

        # The index this group has in the global GroupRegistry. Used to distinguish equally named groups.
        self.group_index: int = -1

        # If the viewer group has file sensors, the user should be allowed to change the payload
        self.wrote_recording: bool = self.has_file_sensors
        self.container: DeltaGenerator = st.container()

        # Weather group will be shown by the GroupRegistry
        self.hidden: bool = False

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self._path = path

        # Notify all associated group members about the new path
        for viewer in self.viewers:
            viewer.sensor.path = self._path

    def viewer_count(self) -> int:
        return len(self.viewers)

    def _toggle_recording(self) -> None:
        for viewer in self.viewers:
            if self.is_recording:
                viewer.sensor.stop_recording()

                # Save group name, path and payload to file
                if self._path:   # Check is redundant as _toggle_recording can only be called when the path is valid
                    ImageWriter.write_attr(file_path=self._path, attribute='group_name', value=self.group_name)
                    ImageWriter.write_attr(file_path=self._path, attribute='path', value=self._path)
                    self._persist_payload()

                self.wrote_recording = True

            else:
                viewer.sensor.start_recording()

        self.is_recording = not self.is_recording

    def _update_stuff(self, clean_container: DeltaGenerator) -> None:
        self.container = clean_container
        self.container.markdown(f'### {self.group_name} (#{self.group_index})')
        self.container.markdown('###### Sensors')
        for viewer in self.viewers:
            viewer.update_container(container=self.container)

    def _render_settings(self) -> None:
        for viewer in self.viewers:
            viewer.render_options()

    def _render_payload(self) -> None:
        self.container.markdown('###### Payload')

        with self.container:
            payload_container = self.container.container(border=True)

            with payload_container:

                # Display info to the user if no payload is available
                if len(self.payload) == 0:
                    st.info(
                        body='No payload has been set for this group. To configure it, please update the payload in '
                             'your group\'s configuration file.',
                        icon='💡'
                    )
                    return

                for index, element in enumerate(self.payload):
                    element_type = element['type']

                    element_key = f'{self.group_index}_{self.group_index}_payload{index}'

                    if element_type == "slider":
                        st.slider(
                            label=element.get("label", "Some slider input"),
                            min_value=element.get("min_value", 0),
                            max_value=element.get("max_value", 100),
                            value=element.get("default", 0),
                            step=1,
                            label_visibility="visible",
                            key=element_key,
                        )

                    elif element_type == "text_input":
                        st.text_input(
                            label=element.get("label", "Some text input"),
                            value=element.get("default", ""),
                            label_visibility="visible",
                            key=element_key,
                        )

                st.button(
                    label="Save changes",
                    type="primary",
                    # Saving of payload only allowed when (1) the file exists and (2) it was written
                    disabled=not (self._path and os.path.exists(self._path) and self.wrote_recording),
                    on_click=self._persist_payload,
                    key=f'{self.group_name}_{self.group_index}_save_changes_key'
                )

    def _persist_payload(self) -> None:

        # Update payload
        for index, element in enumerate(self.payload):
            element_key = f'{self.group_index}_{self.group_index}_payload{index}'
            element["default"] = st.session_state[element_key]

        # Save payload to disk
        ImageWriter.write_attr(file_path=self._path, attribute='payload', value=str(self.payload))

    def _render_data(self) -> None:
        for viewer in self.viewers:
            viewer.render_frame()

    def _render_recording_control(self) -> None:
        self.container.markdown('###### Recording')
        with self.container:
            recording_container = self.container.container(border=True)

            with recording_container:

                # Only groups that don't have any file sensors associated with them, should be allowed to record
                if self.has_file_sensors:
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
                            value=self._path,
                            placeholder="File name (must have .touch extension)",
                            label_visibility="collapsed",
                            disabled=self.is_recording,
                            key=f'{self.group_name}_{self.group_index}_path_key'
                    )

                    # Check if the entered path is valid
                    if path is not None:
                        if os.path.exists(path):
                            st.warning(
                                body=f'The file {path} already exists!',
                                icon='⚠️'
                            )

                        if path != self._path:
                            self.wrote_recording = False

                        # If the path does not already exist, use it as the new path
                        if not path.endswith('.touch'):
                            path = f'{path}.touch'
                        self.path = path

                with right:
                    st.button(
                        label="Stop recording" if self.is_recording else "Start recording",
                        type="primary",
                        # Recording only allowed when (1) file does not exist
                        disabled=not (self._path and not os.path.exists(self._path)),
                        use_container_width=True,
                        on_click=self._toggle_recording,
                        args=(),
                        key=f'{self.group_name}_{self.group_index}_recording_key'
                    )

    def _render_video_control(self):

        def restart_videos():
            for viewer in self.viewers:
                if isinstance(viewer, FileViewer):
                    viewer.restart_video()

        if self.has_file_sensors:
            self.container.markdown('###### Replay panel')
            with self.container:
                video_control_container = self.container.container(border=True)

                with video_control_container:
                    st.button(
                        label="Restart video",
                        type="primary",
                        disabled=False,
                        use_container_width=True,
                        on_click=restart_videos,
                        args=()
                    )

    def _unload_group(self):

        def disconnect():
            # Disconnect sensors
            for viewer in self.viewers:
                viewer.sensor.disconnect()

            # Mark self as hidden
            self.hidden = True

        self.container.markdown('###### Remove group')
        with self.container:
            unload_group_container = self.container.container(border=True)

            with unload_group_container:
                st.button(
                    label="Remove Group",
                    type="primary",
                    disabled=self.is_recording,
                    use_container_width=True,
                    on_click=disconnect,
                    args=(),
                    key=f'{self.group_name}_{self.group_index}_remove_group_key'
                )

    def render_static(self, clean_container: DeltaGenerator) -> None:
        self._update_stuff(clean_container=clean_container)
        self._render_settings()
        self._render_video_control()
        self._render_recording_control()
        self._render_payload()
        self._unload_group()

    def render_dynamic(self) -> None:
        self._render_data()
