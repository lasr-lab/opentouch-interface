import streamlit as st

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.dataclasses.image.image_player import ImagePlayer
from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.sensors.file_sensor import FileSensor


class FileViewer(BaseImageViewer):
    def __init__(self, sensor: FileSensor):
        super().__init__(sensor=sensor)

        self.player: ImagePlayer = self.sensor.sensor

    def render_options(self):
        # Render heading with sensor name
        self.title.markdown(f"##### Sensor '{self.sensor_name}'")

    def restart_video(self):
        self.player.restart()

    def render_frame(self) -> None:
        """Render the current frame to the image widget."""
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
