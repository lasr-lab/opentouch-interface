import random
from abc import abstractmethod

import streamlit as st
from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.options import SetOptions, Streams
from opentouch_interface.touch_sensor import TouchSensor
from streamlit.delta_generator import DeltaGenerator


top = st.empty()
top_divider = st.empty()


class ViewerFactory:
    def __new__(cls, sensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            return DigitViewer(sensor)
        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            return GelsightMiniViewer(sensor)
        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')


class Viewer:
    def __init__(self, sensor: TouchSensor):
        self.sensor: TouchSensor = sensor
        self.image_widget = st.image([])

    @abstractmethod
    def render_options(self, dg: DeltaGenerator, left: DeltaGenerator, right: DeltaGenerator):
        pass

    def get_frame(self):
        return self.sensor.read(Streams.FRAME)

    def update_image_widget(self, dg: DeltaGenerator, left: DeltaGenerator, right: DeltaGenerator):
        self.image_widget = left.image([])

    def get_image_widget(self):
        return self.image_widget

    def render_frame(self):
        frame = self.get_frame()
        image = self.get_image_widget()
        image.image(frame)


class DigitViewer(Viewer):

    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self, dg: DeltaGenerator, left: DeltaGenerator, right: DeltaGenerator):
        right.markdown(f"## Settings for {self.sensor.settings['Name']}")
        resolution = right.selectbox("Resolution", ("QVGA", "VGA"), key="Resolution")
        fps = right.selectbox("FPS", ("30", "60"), key="FPS")
        intensity = right.slider("Brightness", 0, 15, 15, key="Brightness")

        self.sensor.set(SetOptions.INTENSITY, value=int(intensity))
        self.sensor.set(SetOptions.RESOLUTION, value=resolution)
        self.sensor.set(SetOptions.FPS, value=int(fps))


class GelsightMiniViewer(Viewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self, dg: DeltaGenerator, left: DeltaGenerator, right: DeltaGenerator):
        pass


def render_sidebar():
    mapping = {
        "Digit": TouchSensor.SensorType.DIGIT,
        "Gelsight Mini": TouchSensor.SensorType.GELSIGHT_MINI
    }

    st.sidebar.markdown('### Add Sensor')
    selected_sensor = st.sidebar.selectbox(
        label="Select sensor",
        options=("Digit", "Gelsight Mini"),
        placeholder="Sensor type",
        index=None,
        label_visibility="collapsed")

    if selected_sensor is not None:
        selected_sensor = mapping[selected_sensor]

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

        # if 'viewers' not in st.session_state:
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
        sensor = OpentouchInterface(sensor_type=sensor_type)
        sensor.initialize(name=name, serial=serial)
        sensor.connect()

        viewer = ViewerFactory(sensor, sensor_type)
        st.session_state.viewers.append(viewer)


def render_viewers(dg: DeltaGenerator, left: DeltaGenerator, right: DeltaGenerator):
    if 'viewers' in st.session_state:
        for viewer in st.session_state.viewers:
            viewer.update_image_widget(dg, left, right)
            viewer.render_options(dg, left, right)
            # viewer.render_frame()
            dg.divider()

        for viewer in st.session_state.viewers:
            while True:
                viewer.render_frame()


def get_clean_rendering_container(app_state: str) -> DeltaGenerator:
    """Makes sure we can render from a clean slate on state changes."""
    # If app_state != previous_state, "swap" slot_in_use
    slot_in_use = st.session_state.slot_in_use = st.session_state.get("slot_in_use", "a")
    if app_state != st.session_state.get("previous_state", app_state):
        if slot_in_use == "a":
            slot_in_use = st.session_state.slot_in_use = "b"
        else:
            slot_in_use = st.session_state.slot_in_use = "a"

    st.session_state.previous_state = app_state

    slot = {
        "a": st.empty(),
        "b": st.empty(),
    }[slot_in_use]

    return slot.container()


def main():
    top.title('Opentouch Viewer')
    top_divider.divider()
    dg = get_clean_rendering_container(app_state=f"{random.random()}")
    left, right = dg.container().columns(2)
    render_sidebar()
    render_viewers(dg, left, right)


if __name__ == '__main__':
    main()
