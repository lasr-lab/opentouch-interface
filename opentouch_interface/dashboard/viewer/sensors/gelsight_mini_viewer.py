from opentouch_interface.dashboard.viewer.base_viewer import BaseViewer
from opentouch_interface.interface.touch_sensor import TouchSensor


class GelsightMiniViewer(BaseViewer):
    """
    Viewer class for Gelsight Mini sensor.
    """
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self):
        """
        Render options specific to the Gelsight Mini sensor.
        """
        self.right.markdown(f"## Settings for {self.sensor.settings['Name']}")
        self.dg.divider()
