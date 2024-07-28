from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.touch_sensor import TouchSensor


class FileViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """
        sensor_name = self.sensor.config.sensor_name

        # Render heading with sensor name
        self.right.markdown(f"## Settings for {sensor_name}")

        self.right.button(
            label="Restart video",
            on_click=self.sensor.sensor.restart(),
            type="secondary"
        )
