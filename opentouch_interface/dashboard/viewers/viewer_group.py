import os
from typing import List, Dict, Any, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.viewers.image.baes_image_viewer import BaseImageViewer
from opentouch_interface.dashboard.viewers.image.file_viewer import FileViewer
from opentouch_interface.core.dataclasses.image.image_writer import ImageWriter


class ViewerGroup:
    """
    A class that manages a group of image viewers and allows interaction with sensors and file-based payloads.

    The ViewerGroup class provides methods for rendering viewer groups, controlling sensor recordings,
    and handling file-based payloads. It interacts with Streamlit's `DeltaGenerator` for rendering
    components and manages sensor settings for viewers.
    """

    def __init__(self, group_name: str, path: Optional[str], viewers: List[BaseImageViewer],
                 payload: List[Dict[str, Any]]):
        """
        Initializes the ViewerGroup.

        :param group_name: Name of the viewer group.
        :param path: Optional file path for saving recording data.
        :param viewers: List of viewers (instances of BaseImageViewer) associated with the group.
        :param payload: List of dictionaries containing payload data for configuration (e.g., sliders, text inputs).
        """
        self.group_name: str = group_name
        self._path: Optional[str] = path
        self.viewers: List[BaseImageViewer] = viewers or []
        self.payload: List[Dict[str, Any]] = payload

        # Check if any viewers have sensors of type 'FILE'
        self.has_file_sensors: bool = any(viewer.sensor.config.sensor_type == 'FILE' for viewer in self.viewers)

        # Flag to track recording state
        self.is_recording: bool = False

        # The index in the global GroupRegistry (default is -1, meaning unset)
        self.group_index: int = -1

        # If the group has file sensors, allow changes to the payload
        self.wrote_recording: bool = self.has_file_sensors
        self.container: DeltaGenerator = st.container()

        # Determines if the group should be shown by the GroupRegistry
        self.hidden: bool = False

    @property
    def path(self) -> str:
        """
        Getter for the group file path.

        :return: The current file path.
        """
        return self._path

    @path.setter
    def path(self, path: str):
        """
        Setter for the group file path. Notifies all viewers to update their paths.

        :param path: The new file path.
        """
        self._path = path

        # Update the path for all viewers in the group
        for viewer in self.viewers:
            viewer.sensor.path = self._path

    def viewer_count(self) -> int:
        """
        Returns the number of viewers in the group.

        :return: Number of viewers.
        :rtype: int
        """
        return len(self.viewers)

    def _toggle_recording(self) -> None:
        """
        Toggles the recording state of the group's viewers.

        If recording is stopped, the group's name, path, and payload are saved to file. Otherwise, starts recording.
        """
        for viewer in self.viewers:
            if self.is_recording:
                viewer.sensor.stop_recording()

                # Save group name, path, and payload to the file when stopping recording
                if self._path:
                    ImageWriter.write_attr(file_path=self._path, attribute='group_name', value=self.group_name)
                    ImageWriter.write_attr(file_path=self._path, attribute='path', value=self._path)
                    self._persist_payload()

                self.wrote_recording = True
            else:
                viewer.sensor.start_recording()

        self.is_recording = not self.is_recording

    def _update_stuff(self, clean_container: DeltaGenerator) -> None:
        """
        Updates the Streamlit container with the current group name and group index.

        :param clean_container: A new Streamlit container for rendering the updated information.
        :type clean_container: DeltaGenerator
        """
        self.container = clean_container
        self.container.markdown(f'### {self.group_name} (#{self.group_index})')
        self.container.markdown('###### Sensors')
        for viewer in self.viewers:
            viewer.update_container(container=self.container)

    def _render_settings(self) -> None:
        """Renders viewer-specific settings for each viewer in the group."""
        for viewer in self.viewers:
            viewer.render_options()

    def _render_payload(self) -> None:
        """Renders the configuration payload for the group (e.g., sliders, text inputs)."""
        self.container.markdown('###### Payload')

        with self.container:
            payload_container = self.container.container(border=True)

            with payload_container:

                # Display info to the user if no payload is available
                if len(self.payload) == 0:
                    st.info(
                        body="No payload has been set for this group. To configure it, please update the payload in "
                             "your group's configuration file.",
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
        """
        Persists the current payload values to the file system by saving the updated payload to the group's file path.
        """
        for index, element in enumerate(self.payload):
            element_key = f'{self.group_index}_{self.group_index}_payload{index}'
            element["default"] = st.session_state[element_key]

        # Save payload to disk
        ImageWriter.write_attr(file_path=self._path, attribute='payload', value=str(self.payload))

    def _render_data(self) -> None:
        """Renders dynamic data such as live video frames for each viewer."""
        for viewer in self.viewers:
            viewer.render_frame()

    def _render_recording_control(self) -> None:
        """Renders the recording control panel for managing file-based recording."""
        self.container.markdown('###### Recording')
        with self.container:
            recording_container = self.container.container(border=True)

            with recording_container:

                # Only groups that don't have any file sensors associated with them, should be allowed to record
                if self.has_file_sensors:
                    st.info(
                        body="Recording is only available for groups that don't contain file sensors.",
                        icon='💡'
                    )
                    return

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
                            st.warning(f'The file {path} already exists!', icon='⚠️')

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
                        key=f'{self.group_name}_{self.group_index}_recording_key'
                    )

    def _render_video_control(self) -> None:
        """Renders video control settings for viewers associated with file sensors."""
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
                        use_container_width=True,
                        on_click=restart_videos,
                        key=f'{self.group_name}_{self.group_index}_restart_video_key'
                    )

    def _unload_group(self) -> None:
        """Renders controls for unloading (removing) the viewer group from the UI."""
        def disconnect():
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
                    key=f'{self.group_name}_{self.group_index}_remove_group_key'
                )

    def render_static(self, clean_container: DeltaGenerator) -> None:
        """
        Renders the static (non-live) UI components such as settings, video control, recording control, and payload.

        :param clean_container: A Streamlit container for rendering UI elements.
        :type clean_container: DeltaGenerator
        """
        self._update_stuff(clean_container=clean_container)
        self._render_settings()
        self._render_video_control()
        self._render_recording_control()
        self._render_payload()
        self._unload_group()

    def render_dynamic(self) -> None:
        """Renders the dynamic content for the viewers, such as live video frames."""
        self._render_data()
