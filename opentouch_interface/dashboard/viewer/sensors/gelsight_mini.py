from opentouch_interface.dashboard.viewer.viewer import Viewer

from opentouch_interface.touch_sensor import TouchSensor


class GelsightMiniViewer(Viewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self):
        self.right.markdown(f"## Settings for {self.sensor.settings['Name']}")
        self.dg.divider()
