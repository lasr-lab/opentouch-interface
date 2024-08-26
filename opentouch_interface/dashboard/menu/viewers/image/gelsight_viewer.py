from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor

import streamlit as st


class GelsightViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor=sensor)

    def render_options(self) -> None:
        """
        Render options specific to the Digit sensor.
        """

        # Render heading with sensor name
        self.title.markdown(f"##### {self.sensor_name}")

    def render_frame(self) -> None:
        """Render the current frame to the image widget."""
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
