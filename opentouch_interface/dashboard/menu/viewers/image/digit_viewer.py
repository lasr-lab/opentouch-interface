from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.dashboard.util.key_generator import UniqueKeyGenerator
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor

import streamlit as st


class DigitViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor=sensor)

        key_generator: UniqueKeyGenerator = st.session_state.key_generator

        self.streams_key: str = f"streams_{key_generator.get_key()}"
        self.brightness_key: str = f"brightness_{key_generator.get_key()}"
        self.streams_options = ("QVGA, 60 FPS", "VGA, 30 FPS")

        # Keys to store state of select-boxes and sliders in session state
        self.brightness_state = None
        self.streams_state = None

    def render_options(self) -> None:
        """
        Render options specific to the Digit sensor.
        """

        # Render heading with sensor name
        self.title.markdown(f"##### {self.sensor_name}")

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
        with self.right:
            st.selectbox(
                label="Resolution",
                options=self.streams_options,
                on_change=self._update_resolution,
                key=self.streams_key,
                disabled=self.sensor.recording
            )

            st.slider(
                label="Brightness",
                min_value=0,
                max_value=15,
                value=15,
                on_change=self._update_fps,
                key=self.brightness_key,
                disabled=self.sensor.recording
            )

    def _update_fps(self) -> None:
        self.brightness_state = st.session_state[self.brightness_key]
        self.sensor.set(SensorSettings.INTENSITY, value=int(st.session_state[self.brightness_key]))

    def _update_resolution(self) -> None:
        self.streams_state = st.session_state[self.streams_key]

        # Parse selected resolution and FPS
        # FPS don't need to be set as sensor.set() already sets frame rate accordingly to the respective resolution
        resolution, _ = self.streams_state.split(", ")

        self.sensor.set(SensorSettings.RESOLUTION, value=resolution)

    def render_frame(self) -> None:
        """Render the current frame to the image widget."""
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
