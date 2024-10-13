from opentouch_interface.dashboard.viewers.image.baes_image_viewer import BaseImageViewer
from opentouch_interface.core.dataclasses.options import DataStream
from opentouch_interface.core.sensors.touch_sensor import TouchSensor

import streamlit as st


class GelsightViewer(BaseImageViewer):
    """
    Viewer class for displaying Gelsight sensor data in a Streamlit interface.

    The `GelsightViewer` is designed to render live sensor data (e.g., images) from a Gelsight sensor.
    It provides basic functionality for displaying the sensor's frame and rendering any relevant options.
    """

    def __init__(self, sensor: TouchSensor):
        """
        Initializes the GelsightViewer with a TouchSensor instance.

        :param sensor: The Gelsight sensor instance providing the data to display.
        :type sensor: TouchSensor
        """
        super().__init__(sensor=sensor)

    def render_options(self) -> None:
        """
        Render any available options for the Gelsight sensor in the UI.

        Currently, this method only displays the sensor's name as a heading. It can be extended
        to include more options specific to the Gelsight sensor in the future.
        """
        # Display the sensor name as a heading in the UI
        self.title.markdown(f"##### {self.sensor_name}")

    def render_frame(self) -> None:
        """
        Render the current frame from the Gelsight sensor to the image widget.

        This method retrieves the current frame from the sensor and renders it using Streamlit's
        `st.image()` function.
        """
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
