from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.options import SensorSettings
from opentouch_interface.interface.touch_sensor import TouchSensor

import streamlit as st


class DigitViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor=sensor)
        self.sensor_name: str = self.sensor.config.sensor_name
        self.streams_key: str = f"streams_{self.sensor_name}"
        self.brightness_key: str = f"brightness_{self.sensor_name}"
        self.streams_options = ("QVGA, 60 FPS", "VGA, 30 FPS")

        # Keys to store state of select-boxes and sliders in session state
        self.brightness_state = None
        self.streams_state = None

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """

        # Render heading with sensor name
        self.title.markdown(f"### Settings for sensor '{self.sensor_name}'")

        # Check if saved state already is in session state
        if self.brightness_state is None:
            self.brightness_state = self.sensor.get(SensorSettings.INTENSITY)
            st.session_state[self.brightness_key] = self.brightness_state
        else:
            st.session_state[self.brightness_key] = self.brightness_state

        if self.streams_state is None:
            self.streams_state = (f"{self.sensor.get(SensorSettings.RESOLUTION)}, "
                                  f"{self.sensor.get(SensorSettings.FPS)} FPS")
            st.session_state[self.streams_key] = self.streams_state
        else:
            st.session_state[self.streams_key] = self.streams_state

        # Render resolution and slider selection
        self.right.selectbox(
            label="Resolution",
            options=self.streams_options,
            on_change=self.update_resolution,
            key=self.streams_key)

        self.right.slider(
            label="Brightness",
            min_value=0,
            max_value=15,
            value=15,
            on_change=self.update_fps,
            key=self.brightness_key)

    def update_fps(self):
        self.brightness_state = st.session_state[self.brightness_key]
        self.sensor.set(SensorSettings.INTENSITY, value=int(st.session_state[self.brightness_key]))

    def update_resolution(self):
        self.streams_state = st.session_state[self.streams_key]

        # Parse selected resolution and FPS
        resolution, fps = self.streams_state.split(", ")
        fps = int(fps.split()[0])

        self.sensor.set(SensorSettings.RESOLUTION, value=resolution)
        self.sensor.set(SensorSettings.FPS, value=fps)
