import base64
from typing import Optional, Dict, List, Any, Union

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.dashboard.menu.viewers.factory import ViewerFactory
from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry
from opentouch_interface.interface.dataclasses.validation.sensors.digit_config import DigitConfig
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig
from opentouch_interface.interface.dataclasses.validation.validator import Validator
from opentouch_interface.interface.dataclasses.viewer_group import ViewerGroup
from opentouch_interface.interface.opentouch_interface import OpentouchInterface
from opentouch_interface.interface.touch_sensor import TouchSensor


# Only used when entering the sensor config via input fields
class SensorAttribute:
    def __init__(self, value: Optional[str | UploadedFile], required: bool):
        self.value = value
        self.required = required


class SensorForm:
    def __init__(self,
                 sensor_type: Optional[SensorAttribute] = None,
                 name: Optional[SensorAttribute] = None,
                 serial: Optional[SensorAttribute] = None,
                 path: Optional[SensorAttribute] = None,
                 file: Optional[SensorAttribute] = None):

        self.sensor_type = sensor_type or SensorAttribute(None, True)
        self.sensor_name = name or SensorAttribute(None, False)
        self.serial = serial or SensorAttribute(None, False)
        self.path = path or SensorAttribute(None, False)
        self.file = file or SensorAttribute(None, False)

    def is_filled(self) -> bool:
        fields = [self.sensor_name, self.serial, self.path]
        for field in fields:
            if field.required and field.value is None:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        file_content = None
        if self.file is not None and self.file.value:
            file_content = base64.b64encode(self.file.value.getvalue()).decode('utf-8')

        return {
            "sensor_type": self.sensor_type.value,
            "sensor_name": self.sensor_name.value if self.sensor_name is not None else "",
            "serial_id": self.serial.value if self.serial is not None else "",
            "path": self.path.value if self.path is not None else "",
            "file": file_content,
        }


class SensorRegistry:
    def __init__(self):
        self.mapping = {
            "Digit": TouchSensor.SensorType.DIGIT,
            # "Gelsight Mini": TouchSensor.SensorType.GELSIGHT_MINI,
        }

        self.container = st.container(border=False)

    def show(self):
        with self.container:
            st.divider()

            sensor_type = st.selectbox(
                label="Add a new sensor to the dashboard",
                options=self.mapping.keys(),
                index=None,
                placeholder="Select a sensor",
                label_visibility="visible"
            )

            group_name: str = ""
            path: str = ""
            sensors: List[Union[DigitConfig, FileConfig]] = []
            payload: List[Dict[str, Any]] = []

            # The sensor is added manually via an input form
            if sensor_type:
                selected_sensor: TouchSensor.SensorType = self.mapping[sensor_type]
                form: SensorForm = self.render_input_fields(sensor_type=selected_sensor)

                group_name = form.sensor_name.value
                path = form.path.value

                if form.sensor_type.value == 'DIGIT':
                    sensors = [DigitConfig(**form.to_dict())]

                st.button(
                    label="Add sensor",
                    type="primary",
                    disabled=not form.is_filled(),
                    on_click=self.add_group,
                    args=(group_name, path, sensors, payload)
                )

            # The sensor is added via a YAML or touch file
            else:
                file: UploadedFile = st.file_uploader(
                    label="Or choose sensor config",
                    type=['yaml', 'touch'],
                    accept_multiple_files=False,
                    label_visibility="collapsed"
                )

                if file:
                    validator = Validator(file=file)
                    group_name, path, sensors, payload = validator.validate()

                    self.add_group(group_name=group_name, path=path, sensor_configs=sensors, payload=payload)

            if st.session_state.group_registry.viewer_count() == 0:
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
                    label="Where should Digit save it's data?",
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

        # elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
        #     with self.container:
        #         sensor_name = st.text_input(
        #             label="Name your file sensor",
        #             value=None,
        #             placeholder="Sensor name (e.g., Thumb)",
        #             label_visibility="collapsed"
        #         )
        #         sensor_path = st.text_input(
        #             label="Where is the .h5 file located?",
        #             value=None,
        #             placeholder="Path to example.h5 (optional)",
        #             label_visibility="collapsed"
        #         )
        #         return SensorForm(
        #             sensor_type=SensorAttribute(sensor_type.name, True),
        #             name=SensorAttribute(sensor_name, True),
        #             path=SensorAttribute(sensor_path, False)
        #         )

    @staticmethod
    def add_group(group_name: str, path: Optional[str], sensor_configs: List[Union[DigitConfig, FileConfig]],
                  payload: List[Dict[str, Any]]):

        group_registry: GroupRegistry = st.session_state.group_registry
        sensor_names: List[str] = [viewer.sensor.config.sensor_name for viewer in group_registry.get_all_viewers()]
        new_sensor_names: List[str] = [sensor_config.sensor_name for sensor_config in sensor_configs]

        # First, check if there are any non-unique sensor names
        duplicates: List[str] = [name for name in new_sensor_names if name in sensor_names]

        if duplicates:
            st.error(body=f"The sensor names {duplicates} are not unique either inside the group or are already "
                          f"registered in other groups!", icon="⚠️")
            return

        # try:
        # For each sensor config, create a sensor
        viewers: List[BaseImageViewer] = []

        for sensor_config in sensor_configs:
            sensor: TouchSensor = OpentouchInterface(config=sensor_config)
            sensor.initialize()
            sensor.connect()
            sensor.calibrate()

            sensor_type: TouchSensor.SensorType = TouchSensor.SensorType[sensor_config.sensor_type]
            viewer: BaseImageViewer = ViewerFactory(sensor, sensor_type)
            viewers.append(viewer)

            # Create and save the group
            group: ViewerGroup = ViewerGroup(group_name=group_name, path=path, viewers=viewers, payload=payload)
            group_registry.add_group(group=group)

            # Output message
            message = '\n'.join(
                f'{viewer.sensor.config.sensor_name} ({viewer.sensor.config.sensor_type}) \n'
                for viewer in viewers)

            st.success(
                body=f"The following sensors have been successfully added as part of the group '{group_name}': "
                     f"{message}",
                icon="💡"
            )

        # except Exception as e:
        #     st.error(body=e, icon="⚠️")
