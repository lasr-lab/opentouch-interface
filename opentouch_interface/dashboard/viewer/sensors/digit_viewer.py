from opentouch_interface.dashboard.viewer.base_viewer import BaseViewer

from opentouch_interface.interface.options import SetOptions
from opentouch_interface.interface.touch_sensor import TouchSensor


class DigitViewer(BaseViewer):
    """
    Viewer class for Digit sensor.
    """
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """
        self.right.markdown(f"## Settings for {self.sensor.settings['Name']}")
        resolution = self.right.selectbox("Resolution", ("QVGA", "VGA"),
                                          key=f"Resolution_{self.sensor.settings['Name']}")
        fps = self.right.selectbox("FPS", ("30", "60"), key=f"FPS_{self.sensor.settings['Name']}")
        intensity = self.right.slider("Brightness", 0, 15, 15, key=f"Brightness_{self.sensor.settings['Name']}")
        self.dg.divider()

        self.sensor.set(SetOptions.INTENSITY, value=int(intensity))
        self.sensor.set(SetOptions.RESOLUTION, value=resolution)
        self.sensor.set(SetOptions.FPS, value=int(fps))
