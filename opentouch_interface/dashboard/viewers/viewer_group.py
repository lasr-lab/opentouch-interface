import os

import streamlit as st
import yaml
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.core.registries.central_registry import CentralRegistry
from opentouch_interface.core.sensor_group import SensorGroup
from opentouch_interface.dashboard.util.widget_state_manager import WidgetStateManager
from opentouch_interface.dashboard.viewers.base_viewer import BaseViewer
from opentouch_interface.dashboard.viewers.payload_renderer import PayloadRenderer
from opentouch_interface.dashboard.viewers.viewer_factory import ViewerFactory


class TouchDumper(yaml.SafeDumper):
    pass


# Custom representer function for lists
def represent_list_custom(dumper, data):
    if isinstance(data, list) and len(data) == 3 and all(isinstance(item, int) for item in data):
        # Use flow style (i.e., [0, 0, 0])
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
    else:
        # Otherwise, use block style (i.e., each item on its own line)
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)


TouchDumper.add_representer(list, represent_list_custom)


class ViewerGroup:
    """
    Manages a group of sensor viewers, enabling interaction with sensors and file-based payloads.
    """

    def __init__(self, sensor_group: SensorGroup):
        # Initialize placeholders for UI elements in order
        self._title_header = st.empty()  # Placeholder for '<group_name> (#<group_idx>)' text
        self._container = st.empty()  # The surrounding container for a viewer group
        self._config_area = st.empty()  # Container for payload and group settings
        self._sensor_header = st.empty()  # Placeholder for 'Sensors' text

        self._sensor_group = sensor_group

        # Initialize viewers for each sensor in the group
        self.viewers: list[BaseViewer] = [ViewerFactory(sensor=sensor) for sensor in sensor_group.sensors]

        # Metadata and state
        self._group_idx: int = -1  # Index in the global registry (default is unset)
        self.hidden: bool = False  # Visibility state in GroupRegistry

        # Register this ViewerGroup in the global registry
        CentralRegistry.viewer_group_registry().add(self)

        # Renderer for payload
        self._payload_renderer: PayloadRenderer = PayloadRenderer(
            payload=sensor_group.payload, group_idx=self._group_idx
        )

        # Key for naming widget-keys
        self._key_prefix = f'{self.group_name}_{self._group_idx}'

        # Keeps the value of a widget even after switching pages
        self._state_manager = WidgetStateManager()

    # Properties for easy access to group metadata
    @property
    def group_name(self) -> str:
        return self._sensor_group.group_name

    @property
    def source(self):
        return self._sensor_group.source

    @property
    def destination(self) -> str:
        return self._sensor_group.destination

    @property
    def viewer_count(self) -> int:
        return len(self.viewers)

    @property
    def _is_recording(self) -> bool:
        return self._sensor_group.is_recording

    @property
    def _dest_candidate(self) -> str:
        key = self._state_manager.unique_key('destination_input')
        return st.session_state.get(key, self.destination)

    # Public methods
    def update_container(self, container: DeltaGenerator):
        """Update all subsequent containers of this viewer group. Necessary to remove shadow elements."""
        self._container = container.container()
        self._title_header = self._container.empty()
        self._config_area = self._container.container()
        self._sensor_header = self._container.empty()

        for viewer in self.viewers:
            viewer.update_container(self._container)

    def render_static(self):
        """Render the static content of the viewer group."""
        header_text = f'{self.group_name} (from {self.source})' if self.source not in {self.group_name,
                                                                                       ''} else self.group_name
        self._title_header.markdown(f'### {header_text}')

        # Render configuration and payload headline
        left_ratio = 0.6
        left, right = self._config_area.columns([left_ratio, 1 - left_ratio])
        with left:
            # Check, where the payload is updated
            text = ''
            if os.path.isfile(self._sensor_group.abs_destination):
                text = f'(saving to `{self.destination}`)'
            elif os.path.isfile(self._sensor_group.abs_source):
                text = f'(saving to `{self.source}`)'
            st.markdown(f'##### Payload {text}')
        with right:
            st.markdown('##### Group Settings')

        # Render payload and group settings
        left, right = self._config_area.columns([left_ratio, 1 - left_ratio], border=True)
        with left.container(border=False):
            # Use st.empty().container() to eliminate shadow elements
            with st.empty().container():
                self._payload_renderer.render()
        with right:
            self._render_group_settings()

        # Render static sensor content for each viewer (e.g.settings)
        self._sensor_header.markdown('##### Sensors')
        for viewer in self.viewers:
            viewer.render_static_content()

    def render_dynamic(self):
        # Render data
        for viewer in self.viewers:
            viewer.render_dynamic_content()

    def disconnect(self):
        self._sensor_group.disconnect()

    def _render_group_settings(self):
        """Render the group settings UI elements."""

        # Row 1: Remove group and download config
        left, right = st.columns(2)
        with left:
            st.button(label="Remove Group",
                      type="secondary",
                      use_container_width=True,
                      icon=':material/delete:',
                      key=f'{self._key_prefix}_remove_group_key',
                      disabled=self._is_recording,
                      on_click=CentralRegistry.viewer_group_registry().remove_and_unload,
                      args=(self,)
                      )
        with right:
            yaml_config = yaml.dump(self._sensor_group.get_config(), Dumper=TouchDumper, sort_keys=False)
            st.download_button(
                label="Download Config",
                data=yaml_config,
                file_name=f'{self._key_prefix}_config.yaml',
                key=f'{self._key_prefix}_download_button_key',
                use_container_width=True,
                icon=':material/download:'
            )

        # Row 2: Destination input, save destination
        left, right = st.columns([0.75, 0.25], vertical_alignment='bottom')
        self._state_manager.init_state('destination_input', self.destination)
        with left:
            st.text_input(
                label='Save recording to',
                key=self._state_manager.unique_key('destination_input'),
                placeholder='e.g. my_recording',
                disabled=self._is_recording
            )

        if os.path.exists(os.path.join('datasets', self._dest_candidate)) and not self._is_recording:
            st.warning('This dataset already exists!')

        # Clear shadow warning elements
        st.empty()

        with right:
            dest_not_ok = not self._dest_candidate or os.path.exists(
                os.path.join('datasets', self._dest_candidate))
            st.button(
                label='',
                icon=':material/save:',
                use_container_width=True,
                help='Save new destination',
                disabled=self._is_recording or dest_not_ok or self.destination == self._dest_candidate,
                key=f'{self._key_prefix}_save_destination_button_key',
                on_click=self._sensor_group.set_destination, args=(self._dest_candidate,)
            )

        # Row 3: Toggle recording
        left, mid, right = st.columns([0.5, 0.25, 0.25], vertical_alignment='bottom')
        with left:
            button_text = 'Start Recording' if not self._is_recording else 'Stop Recording'
            st.button(
                label=button_text,
                icon=':material/radio_button_checked:',
                use_container_width=True,
                help='Toggle recording',
                # Starting the recording is forbidden when the file already exists
                disabled=not self._is_recording and os.path.exists(os.path.join('datasets', self.destination)),
                on_click=self._toggle_recording,
                args=(),
                key=f'{self._key_prefix}_toggle_recording_button_key'
            )

        with mid:
            has_replay_mode_sensors = any(viewer.sensor.get('replay_mode') for viewer in self.viewers)
            st.text_input(
                label='Jump to',
                value='0:00',
                max_chars=5,
                key=f'{self._key_prefix}_jump_to_recording_text_input_key',
                placeholder='mm:ss',
                disabled=(not has_replay_mode_sensors) or self._is_recording
            )

        with right:
            has_replay_mode_sensors = any(viewer.sensor.get('replay_mode') for viewer in self.viewers)
            st.button(label='',
                      icon=':material/replay:',
                      type='primary', help='Restart replay',
                      key=f'restart_replay_{self._group_idx}',
                      use_container_width=True,
                      disabled=(not has_replay_mode_sensors) or self._is_recording,
                      on_click=self._restart_replay,
                      args=()
                      )

        # Clear shadow toggle recording and restart replay elements
        st.empty()

    def _restart_replay(self):
        """
        Restart replay from the time specified in the 'Jump to' input field.
        The time can be specified in 'mm:ss' format (e.g., '1:30' for 1 minute and 30 seconds).
        If an invalid format is provided, the replay will start from the beginning (0:00).
        """
        # Get the time input from the 'Jump to' field
        time_input = st.session_state.get(f'{self._key_prefix}_jump_to_recording_text_input_key', '0:00')

        # Default to 0 seconds if parsing fails
        offset_seconds = 0.0

        try:
            # Handle different input formats
            if ':' in time_input:
                parts = time_input.split(':')
                if len(parts) == 2:
                    minutes, seconds = parts
                    offset_seconds = int(minutes) * 60 + int(seconds)
            else:
                # If only a number is entered, assume it's seconds
                offset_seconds = float(time_input)
        except (ValueError, TypeError):
            # Silently fall back to 0:00 for any parsing errors
            offset_seconds = 0.0

        # Start replay with the calculated offset
        # print(f"Jumping to {offset_seconds} seconds from the beginning of the recording.")
        self._sensor_group.start_replay(offset_seconds)

    def _toggle_recording(self):
        """Toggle the recording state."""
        if self._is_recording:
            self._sensor_group.stop_recording()
        else:
            # Update view
            st.session_state[self._state_manager.unique_key('destination_input')] = self.destination
            self._sensor_group.start_recording()
