import streamlit as st

from opentouch_interface.dashboard.viewers.image.baes_image_viewer import BaseImageViewer
from opentouch_interface.core.dataclasses.image.image_player import ImagePlayer
from opentouch_interface.core.dataclasses.options import DataStream
from opentouch_interface.core.sensors.file_sensor import FileSensor


class FileViewer(BaseImageViewer):
    """
    Viewer class for displaying data from a FileSensor, typically rendering video frames.

    The `FileViewer` allows users to view sensor data (e.g., video frames) from files, providing
    basic controls for rendering the current frame and restarting the video.
    """

    def __init__(self, sensor: FileSensor):
        """
        Initializes the FileViewer with a FileSensor and its associated ImagePlayer.

        :param sensor: The FileSensor that provides the data to be displayed.
        :type sensor: FileSensor
        """
        super().__init__(sensor=sensor)

        # ImagePlayer is responsible for handling video playback
        self.player: ImagePlayer = self.sensor.sensor

    def render_options(self) -> None:
        """
        Render viewer-specific options in the UI.

        This method displays the sensor name as a heading, but no additional options are provided
        since FileViewer does not require specific settings like brightness or resolution.
        """
        # Render the sensor name as a heading
        self.title.markdown(f"##### Sensor '{self.sensor_name}'")

    def restart_video(self) -> None:
        """
        Restart the video from the beginning.

        This method resets the video playback to the start using the ImagePlayer's `restart` method.
        """
        self.player.restart()

    def render_frame(self) -> None:
        """
        Render the current frame from the file sensor to the image widget.

        This method retrieves the current video frame from the sensor and displays it in the UI using
        Streamlit's `st.image()` function.
        """
        frame = self.sensor.read(DataStream.FRAME)
        if frame and self.image_widget:
            with self.image_widget:
                st.image(frame.as_cv2())
