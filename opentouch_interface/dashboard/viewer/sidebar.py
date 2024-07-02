from opentouch_interface.dashboard.viewer.viewer_factory import ViewerFactory
from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.touch_sensor import TouchSensor
import streamlit as st


class Sidebar:
    def __init__(self):
        self.mapping = {
            "Digit": TouchSensor.SensorType.DIGIT,
            "Gelsight Mini": TouchSensor.SensorType.GELSIGHT_MINI
        }

    def render(self):
        st.sidebar.markdown('### Add Sensor')
        selected_sensor = st.sidebar.selectbox(
            label="Select sensor",
            options=("Digit", "Gelsight Mini"),
            placeholder="Sensor type",
            index=None,
            label_visibility="collapsed")

        if selected_sensor is not None:
            selected_sensor = self.mapping[selected_sensor]

        serial = None
        if selected_sensor == TouchSensor.SensorType.DIGIT:
            serial = st.sidebar.text_input(
                label="Serial identification",
                placeholder="Serial ID",
                label_visibility="collapsed")

        if selected_sensor:
            name = st.sidebar.text_input(
                label="Sensor name",
                placeholder="Choose a name (e.g., 'Thumb')",
                label_visibility="collapsed")

            st.sidebar.button(
                label="Add Sensor",
                use_container_width=True,
                type="primary",
                disabled=(selected_sensor == TouchSensor.SensorType.DIGIT and not serial),
                on_click=add_viewer, args=(selected_sensor, name, serial))


def add_viewer(sensor_type: TouchSensor.SensorType, name: str, serial: str):
    if 'viewers' not in st.session_state:
        st.session_state.viewers = []

    exists = False
    for viewer in st.session_state.viewers:
        exists = exists or (viewer.sensor.settings['Name'] == name)

    if not exists:
        print(f"Added {name} to sensors")
        sensor = OpentouchInterface(sensor_type=sensor_type)
        sensor.initialize(name=name, serial=serial, path="")
        sensor.connect()

        viewer = ViewerFactory(sensor, sensor_type)
        st.session_state.viewers.append(viewer)
