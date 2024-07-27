import os.path
from io import StringIO, BytesIO
from typing import Optional
from datetime import datetime

import streamlit as st
import yaml
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.dashboard.menu.viewers.factory import ViewerFactory
from opentouch_interface.interface.opentouch_interface import OpentouchInterface
from opentouch_interface.interface.options import SensorSettings
from opentouch_interface.interface.touch_sensor import TouchSensor


class SensorAttribute:
    def __init__(self, value: Optional[str | UploadedFile], required: bool):
        self.value = value
        self.required = required


class SensorForm:
    def __init__(self,
                 name: Optional[SensorAttribute] = None,
                 serial: Optional[SensorAttribute] = None,
                 path: Optional[SensorAttribute] = None,
                 file: Optional[SensorAttribute] = None):

        self.name = name or SensorAttribute(None, False)
        self.serial = serial or SensorAttribute(None, False)
        self.path = path or SensorAttribute(None, False)
        self.file = file or SensorAttribute(None, False)

    def is_filled(self) -> bool:
        fields = [self.name, self.serial, self.path]
        for field in fields:
            if field.required and field.value is None:
                return False
        return True


class SensorRegistry:
    def __init__(self):
        self.mapping = {
            "Digit": TouchSensor.SensorType.DIGIT,
            "Gelsight Mini": TouchSensor.SensorType.GELSIGHT_MINI,
            "File": TouchSensor.SensorType.FILE
        }

        self.from_type = {value: key for key, value in self.mapping.items()}

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

            if sensor_type is None:
                config = st.file_uploader(
                    label="Or choose sensor config",
                    type=['yaml'],
                    accept_multiple_files=False,
                    label_visibility="collapsed"
                )
                if config is not None:
                    stringio = StringIO(config.getvalue().decode("utf-8"))
                    config = yaml.safe_load(stringio)
                    form = SensorForm(
                        name=SensorAttribute(config['name'], False),
                        serial=SensorAttribute(config['serial_id'], False),
                        path=SensorAttribute(config['path'], False)
                    )
                    self.add_sensor(sensor_type=TouchSensor.SensorType[config['type']], form=form)

            if sensor_type is not None:
                selected_sensor = self.mapping[sensor_type]

            if sensor_type:
                form = self.render_input_fields(sensor_type=selected_sensor)
                st.button(
                    label="Add sensor",
                    type="primary",
                    disabled=not form.is_filled(),
                    on_click=self.add_sensor,
                    args=(selected_sensor, form)
                )

            if 'viewers' not in st.session_state or len(st.session_state.viewers) == 0:
                st.info(
                    body="To add a new sensor to the 'Live View' page, you can either manually enter the sensor "
                         "details or select a YAML file containing the sensor's configuration.",
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
                    placeholder="Path to example.h5 (optional)",
                    label_visibility="collapsed"
                )
            return SensorForm(
                name=SensorAttribute(sensor_name, True),
                serial=SensorAttribute(serial_id, True),
                path=SensorAttribute(sensor_path, False)
            )

        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            with self.container:
                sensor_name = st.text_input(
                    label="Name your file sensor",
                    value=None,
                    placeholder="Sensor name (e.g., Thumb)",
                    label_visibility="collapsed"
                )
                sensor_path = st.text_input(
                    label="Where is the .h5 file located?",
                    value=None,
                    placeholder="Path to example.h5 (optional)",
                    label_visibility="collapsed"
                )
                return SensorForm(
                    name=SensorAttribute(sensor_name, True),
                    path=SensorAttribute(sensor_path, False)
                )

        elif sensor_type == TouchSensor.SensorType.FILE:
            with self.container:
                sensor_name = st.text_input(
                    label="Name your file sensor",
                    value=None,
                    placeholder="Sensor name (e.g., Thumb)",
                    label_visibility="collapsed"
                )

                file = st.file_uploader(
                    label="Upload your .h5 file",
                    type=['h5'],
                    accept_multiple_files=False,
                    label_visibility="collapsed"
                )

                return SensorForm(
                    name=SensorAttribute(sensor_name, True),
                    file=SensorAttribute(file, True)
                )

    def add_sensor(self, sensor_type: TouchSensor.SensorType, form: SensorForm):
        # If not already existent, create a list for viewers in session state
        if 'viewers' not in st.session_state:
            st.session_state.viewers = []

        # Check if a sensor with that name already exists
        if any(e.sensor.settings[SensorSettings.SENSOR_NAME] == form.name.value for e in st.session_state.viewers):
            st.error(body=f"Sensor named '{form.name.value}' already exists!", icon="⚠️")
            return

        # For each sensor type, check if its arguments are valid
        sensor = OpentouchInterface(sensor_type=sensor_type)
        serial, name, path = form.serial.value, form.name.value, form.path.value
        file: UploadedFile = form.file.value

        if sensor_type == TouchSensor.SensorType.DIGIT:

            # If path is None, choose current date as file name
            if path is None:
                now = datetime.now()
                path = now.strftime("%Y-%m-%d-%H:%M:%S.h5")

            if not path.endswith('.h5'):
                st.error(body=f"File {path} does not end with .h5!", icon="⚠️")
                return
            if os.path.exists(path):
                st.error(body=f"File {path} already exists!", icon="⚠️")
                return
            sensor.initialize(name=name, serial=serial, path=path)

        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:

            # If path is None, choose current date as file name
            if path is None:
                now = datetime.now()
                path = now.strftime("%Y-%m-%d-%H:%M:%S.h5")

            if not path.endswith('.h5'):
                st.error(body=f"File {path} does not end with .h5!", icon="⚠️")
                return
            if os.path.exists(path):
                st.error(body=f"File {path} already exists!", icon="⚠️")
                return
            sensor.initialize(name=name, serial=serial, path=path)

        elif sensor_type == TouchSensor.SensorType.FILE:
            file_or_path = BytesIO(file.getvalue()) if file is not None else path
            sensor.initialize(name=name, serial=serial, path=file_or_path)

        sensor.connect()

        # Create viewer and add it to the session state
        viewer = ViewerFactory(sensor, sensor_type)
        st.session_state.viewers.append(viewer)
        st.success(
            body=f"Sensor {form.name.value} ({self.from_type[sensor_type]}) has been successfully added!",
            icon="💡"
        )
