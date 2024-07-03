from opentouch_interface.dashboard.viewer.base_viewer import BaseViewer

from opentouch_interface.interface.options import SensorSettings
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
        sensor_name = self.sensor.settings[SensorSettings.SENSOR_NAME]

        # Render heading with sensor name
        self.right.markdown(f"## Settings for {sensor_name}")

        # Render resolution selection
        streams_key = f"streams_{sensor_name}"
        streams_options = ("QVGA, 30 FPS", "VGA, 60 FPS")
        streams = self.right.selectbox("Resolution", streams_options, key=streams_key)

        # Parse selected resolution and FPS
        resolution, fps = streams.split(", ")
        fps = int(fps.split()[0])

        # Render brightness slider
        brightness_key = f"Brightness_{sensor_name}"
        intensity = self.right.slider("Brightness", 0, 15, 15, key=brightness_key)

        # Set sensor settings based on user selections
        self.sensor.set(SensorSettings.INTENSITY, value=int(intensity))
        self.sensor.set(SensorSettings.RESOLUTION, value=resolution)
        self.sensor.set(SensorSettings.FPS, value=fps)
