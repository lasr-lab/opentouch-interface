import streamlit as st

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor


class FileViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor=sensor)

    def render_options(self):
        # Render heading with sensor name
        self.title.markdown(f"##### Sensor '{self.sensor_name}'")

        with self.right:
            st.button(
                label="Restart video",
                on_click=self._restart_videos(),
                type="secondary"
            )

    def _restart_videos(self):
        self.sensor.sensor.restart(sensor_name=self.sensor_name)

    def render_frame(self) -> None:
        """Render the current frame to the image widget."""
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
