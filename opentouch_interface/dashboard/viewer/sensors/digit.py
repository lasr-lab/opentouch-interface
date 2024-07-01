from opentouch_interface.dashboard.viewer.viewer import Viewer

from opentouch_interface.options import SetOptions
from opentouch_interface.touch_sensor import TouchSensor


class DigitViewer(Viewer):

    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self):
        self.right.markdown(f"## Settings for {self.sensor.settings['Name']}")
        resolution = self.right.selectbox("Resolution", ("QVGA", "VGA"),
                                          key=f"Resolution_{self.sensor.settings['Name']}")
        fps = self.right.selectbox("FPS", ("30", "60"), key=f"FPS_{self.sensor.settings['Name']}")
        intensity = self.right.slider("Brightness", 0, 15, 15, key=f"Brightness_{self.sensor.settings['Name']}")
        self.dg.divider()

        self.sensor.set(SetOptions.INTENSITY, value=int(intensity))
        self.sensor.set(SetOptions.RESOLUTION, value=resolution)
        self.sensor.set(SetOptions.FPS, value=int(fps))
