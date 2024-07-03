from opentouch_interface.dashboard.viewer.base_viewer import BaseViewer

from opentouch_interface.interface.options import SensorSettings
from opentouch_interface.interface.touch_sensor import TouchSensor


class FileViewer(BaseViewer):
    """
    Viewer class for Digit sensor.
    """

    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """
        sensor_name = self.sensor.settings[SensorSettings.SENSOR_NAME]

        # Render heading with sensor name
        self.right.markdown(f"## Settings for {sensor_name}")
