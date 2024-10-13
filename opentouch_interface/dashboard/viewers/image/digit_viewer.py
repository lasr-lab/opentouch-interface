from opentouch_interface.dashboard.viewers.image.baes_image_viewer import BaseImageViewer
from opentouch_interface.dashboard.util.key_generator import UniqueKeyGenerator
from opentouch_interface.core.dataclasses.options import SensorSettings, DataStream
from opentouch_interface.core.sensors.touch_sensor import TouchSensor

import streamlit as st


class DigitViewer(BaseImageViewer):
    """
    Viewer class for handling Digit sensor data and rendering its options and frames in a Streamlit interface.

    This viewer allows users to control the resolution and brightness of the Digit sensor, as well as
    display live frames captured by the sensor.
    """

    def __init__(self, sensor: TouchSensor):
        """
        Initializes the DigitViewer with a sensor and sets up Streamlit session keys for managing state.

        :param sensor: The Digit sensor instance to interact with.
        :type sensor: TouchSensor
        """
        super().__init__(sensor=sensor)

        # Generate unique keys for session state handling
        key_generator: UniqueKeyGenerator = st.session_state.key_generator
        self.streams_key: str = f"streams_{key_generator.get_key()}"
        self.brightness_key: str = f"brightness_{key_generator.get_key()}"
        self.streams_options = ("QVGA, 60 FPS", "VGA, 30 FPS")

        # State variables for storing select-box and slider states
        self.brightness_state = None
        self.streams_state = None

    def render_options(self) -> None:
        """
        Render user options for configuring the Digit sensor, including resolution and brightness.

        This method uses Streamlit components (selectbox and slider) to let users adjust the sensor's
        resolution and brightness. The values are stored in Streamlit's session state.
        """

        # Render the sensor name as a heading
        self.title.markdown(f"##### {self.sensor_name}")

        # Initialize session state for brightness if not already done
        if self.brightness_state is None:
            self.brightness_state = self.sensor.get(SensorSettings.INTENSITY)
            st.session_state[self.brightness_key] = self.brightness_state
        else:
            st.session_state[self.brightness_key] = self.brightness_state

        # Initialize session state for streams (resolution and FPS) if not already done
        if self.streams_state is None:
            self.streams_state = (f"{self.sensor.get(SensorSettings.RESOLUTION)}, "
                                  f"{self.sensor.get(SensorSettings.FPS)} FPS")
            st.session_state[self.streams_key] = self.streams_state
        else:
            st.session_state[self.streams_key] = self.streams_state

        # Render the resolution select box and brightness slider in the right column
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
                value=st.session_state[self.brightness_key],
                on_change=self._update_fps,
                key=self.brightness_key,
                disabled=self.sensor.recording
            )

    def _update_fps(self) -> None:
        """
        Update the sensor's brightness based on the slider's current value in session state.
        """
        self.brightness_state = st.session_state[self.brightness_key]
        self.sensor.set(SensorSettings.INTENSITY, value=int(self.brightness_state))

    def _update_resolution(self) -> None:
        """
        Update the sensor's resolution based on the user's selection from the resolution select box.
        """
        self.streams_state = st.session_state[self.streams_key]

        # Parse the selected resolution (FPS is already managed by the sensor's resolution setting)
        resolution, _ = self.streams_state.split(", ")

        self.sensor.set(SensorSettings.RESOLUTION, value=resolution)

    def render_frame(self) -> None:
        """
        Render the current frame from the sensor to the image widget.

        This method captures the current frame from the sensor's data stream and displays it using Streamlit.
        """
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
