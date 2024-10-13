from typing import Optional, Dict, List, Any, Union

import streamlit as st
import yaml
from code_editor import code_editor
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.dashboard.viewers.image.baes_image_viewer import BaseImageViewer
from opentouch_interface.dashboard.viewers.group_registry import GroupRegistry
from opentouch_interface.dashboard.viewers.viewer_factory import ViewerFactory
from opentouch_interface.dashboard.viewers.viewer_group import ViewerGroup
from opentouch_interface.core.validation.sensor_config import SensorConfig
from opentouch_interface.core.validation.validator import Validator
from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.core.sensors.touch_sensor import TouchSensor


# Only used when entering the sensor config via input fields
class SensorAttribute:
    def __init__(self, value: Optional[str], required: bool):
        self.value = value
        self.required = required


class SensorForm:
    def __init__(self,
                 sensor_type: Optional[SensorAttribute] = None,
                 name: Optional[SensorAttribute] = None,
                 serial: Optional[SensorAttribute] = None,
                 path: Optional[SensorAttribute] = None):

        # Initialize attributes, only include those with non-None values
        self.attributes: Dict[str, Optional[SensorAttribute]] = {
            "sensor_type": sensor_type or SensorAttribute(None, True),
            "sensor_name": name or SensorAttribute(None, False),
            "serial_id": serial or SensorAttribute(None, False),
            "path": path or SensorAttribute(None, False)
        }

    def is_filled(self) -> bool:
        # Check if all required attributes have values
        return all(attr.value is not None for attr in self.attributes.values() if attr.required)

    def to_dict(self) -> Dict[str, str]:
        # Convert attributes to a dictionary, only with non-None values
        return {key: attr.value for key, attr in self.attributes.items()}


class SensorRegistry:
    def __init__(self):
        self.mapping = {
            "Digit": TouchSensor.SensorType.DIGIT,
            "Gelsight Mini": TouchSensor.SensorType.GELSIGHT_MINI,
        }

        self.container = st.container(border=False)

    def show(self):
        with self.container:
            st.divider()

            # Sensor selection dropdown
            sensor_type = self._select_sensor_type()

            if sensor_type:
                self._handle_manual_sensor_addition(sensor_type)
            else:
                self._handle_file_upload_sensor_addition()

    def _select_sensor_type(self) -> Optional[str]:
        """Select a sensor type from dropdown."""
        return st.selectbox(
            label="Add a new sensor to the dashboard",
            options=self.mapping.keys(),
            index=None,
            placeholder="Select a sensor",
            label_visibility="visible"
        )

    def _handle_manual_sensor_addition(self, sensor_type: str) -> None:
        """Handle manually adding a sensor via form input."""
        selected_sensor: TouchSensor.SensorType = self.mapping[sensor_type]
        form: SensorForm = self.render_input_fields(sensor_type=selected_sensor)

        yaml_config: Optional[Dict[str, str]] = None
        if form.is_filled():
            form_dict = form.to_dict()
            yaml_config = {
                'group_name': form_dict['sensor_name'],
                'path': form_dict['path'],
                'sensors': [form_dict],
                'payload': [],
            }

        # Add sensor button
        st.button(
            label="Add sensor",
            type="primary",
            disabled=not yaml_config,
            on_click=lambda: self.add_group(yaml_config)
        )

    def _handle_file_upload_sensor_addition(self) -> None:
        """Handle sensor addition via YAML or .touch file upload."""
        file: UploadedFile = st.file_uploader(
            label="Or choose sensor config",
            type=['yaml', 'touch'],
            accept_multiple_files=False,
            label_visibility="collapsed"
        )

        if file:
            # Display code editor if it's a YAML file
            if file.name.endswith('.yaml'):
                self._process_yaml_file(file)
            else:
                self.add_group(config=file)
        else:
            # Display info message if no sensors are added
            if not st.session_state.group_registry.viewer_count():
                self._show_info_message()

    def _process_yaml_file(self, file: UploadedFile) -> None:
        """Process and update the YAML file before adding sensor."""
        content = file.read().decode("utf-8")
        response = code_editor(content, lang="yaml")

        left, right = st.columns(2)
        has_error, updated_config = self._parse_yaml(response['text'] or content)

        with right:
            if has_error:
                st.error("Invalid YAML format.")
            else:
                st.success("Updated your sensor config.")

        with left:
            st.info(body="Press Ctrl+Return to save your changes", icon="💡")

            st.button(
                label="Add sensor",
                type="primary",
                disabled=not updated_config,
                use_container_width=True,
                on_click=lambda: self.add_group(updated_config)
            )

    @staticmethod
    def _parse_yaml(content: str) -> (bool, Optional[Dict]):
        """Parse YAML content, returning if there was an error and the parsed config."""
        try:
            return False, yaml.safe_load(content)
        except yaml.YAMLError:
            return True, None

    @staticmethod
    def _show_info_message() -> None:
        """Show an info message if no sensors are added."""
        st.info(
            body="To add a new sensor to the 'Live View' page, you can either manually enter the sensor "
                 "details or select a YAML or .touch file containing the sensor's configuration.",
            icon="💡"
        )

    def render_input_fields(self, sensor_type: TouchSensor.SensorType) -> SensorForm:
        if sensor_type == TouchSensor.SensorType.DIGIT:
            with self.container:
                serial_id = st.text_input(
                    label="Enter Digit's serial number",
                    value=None,
                    placeholder="Serial ID",
                    label_visibility="collapsed"
                )
                sensor_name = st.text_input(
                    label="Enter Digit's name",
                    value=None,
                    placeholder="Sensor name (e.g., Thumb)",
                    label_visibility="collapsed"
                )
                sensor_path = st.text_input(
                    label="Where should Digit save its data?",
                    value=None,
                    placeholder="Path to example.touch (optional)",
                    label_visibility="collapsed"
                )
            return SensorForm(
                sensor_type=SensorAttribute(sensor_type.name, True),
                name=SensorAttribute(sensor_name, True),
                serial=SensorAttribute(serial_id, True),
                path=SensorAttribute(sensor_path, False)
            )

        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            with self.container:
                sensor_name = st.text_input(
                    label="Enter GelsightMini's name",
                    value=None,
                    placeholder="Sensor name (e.g., Thumb)",
                    label_visibility="collapsed"
                )
                sensor_path = st.text_input(
                    label="Where should GelsightMini save its data?",
                    value=None,
                    placeholder="Path to example.touch (optional)",
                    label_visibility="collapsed"
                )
                return SensorForm(
                    sensor_type=SensorAttribute(sensor_type.name, True),
                    name=SensorAttribute(sensor_name, True),
                    path=SensorAttribute(sensor_path, False)
                )

    @staticmethod
    def add_group(config: Union[UploadedFile, Dict[str, str]]):
        group_name: str
        path: Optional[str]
        sensor_configs: List[Union[SensorConfig]]
        payload: List[Dict[str, Any]]

        try:
            validator = Validator(file=config)
            group_name, path, sensor_configs, payload = validator.validate()
            group_registry: GroupRegistry = st.session_state.group_registry

            # For each sensor config, create a sensor
            viewers: List[BaseImageViewer] = []

            progress_bar = st.progress(0)
            for index, sensor_config in enumerate(sensor_configs):
                progress = index / len(sensor_configs)
                progress_bar.progress(value=progress, text=f'Initializing sensor {sensor_config.sensor_name}')

                sensor: TouchSensor = OpentouchInterface(config=sensor_config)
                sensor.initialize()
                sensor.connect()
                sensor.calibrate()

                sensor_type: TouchSensor.SensorType = TouchSensor.SensorType[sensor_config.sensor_type]
                viewer: BaseImageViewer = ViewerFactory(sensor=sensor, sensor_type=sensor_type)
                viewers.append(viewer)

            progress_bar.progress(value=100, text='Finished')

            # Create and save the group
            group: ViewerGroup = ViewerGroup(group_name=group_name, path=path, viewers=viewers, payload=payload)
            group_registry.add_group(group=group)

            # Output message
            message = '\n'.join(
                f'- {viewer.sensor.config.sensor_name} ({viewer.sensor.config.sensor_type}) \n'
                for viewer in viewers)

            st.success(
                body=f"The following sensors have been successfully added as part of the group **{group_name}**: "
                     f"\n\n{message}",
                icon="💡"
            )

        except Exception as e:
            st.error(body=e, icon="⚠️")


st.title('Opentouch Viewer')

sensor_registry = SensorRegistry()
sensor_registry.show()
