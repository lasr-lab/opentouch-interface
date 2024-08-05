from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor


class FileViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

        self.sensor_names = self.sensor.sensor.get_sensor_names()
        self.image_widgets = []

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """
        sensor_name = self.sensor.config.sensor_name

        # Render heading with sensor name
        self.right.markdown(f"## Settings for {sensor_name}")

        self.right.button(
            label="Restart video",
            on_click=self.restart_videos(),
            type="secondary"
        )

    def restart_videos(self):
        for sensor_name in self.sensor_names:
            self.sensor.sensor.restart(sensor_name=sensor_name)

    def get_frame(self, sensor_name: str):
        """
        Get the current frame from the sensor.
        """

        frame = self.sensor.read(DataStream.FRAME, sensor_name=sensor_name)
        if frame is not None:
            return frame.as_cv2()
        return None

    def update_delta_generator(self, dg: DeltaGenerator):
        """
        Update the delta generator for rendering frames.
        """
        self.container = dg.container(border=True)
        self.title = self.container.empty()
        self.left, self.right = self.container.columns(2)
        self.dg = dg
        self.image_widgets = [self.left.image([]) for _ in range(len(self.sensor_names))]

    def render_frame(self):
        """
        Render the current frame to the image widget.
        """

        for index, sensor_name in enumerate(self.sensor_names):
            frame = self.get_frame(sensor_name=sensor_name)

            if frame is not None and self.image_widgets[index] is not None:
                self.image_widgets[index].image(frame)
