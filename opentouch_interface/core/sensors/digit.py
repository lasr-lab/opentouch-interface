from typing import Any

from opentouch_interface.core.registries.class_registries import SensorClassRegistry
from opentouch_interface.core.sensors.interfaces.digit_interface import Digit
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.core.validation.sensors.digit_config import DigitConfig


@SensorClassRegistry.register_sensor('Digit')
class DigitSensor(TouchSensor):
    """
    A class representing a Digit touch sensor, inheriting from TouchSensor. This class
    manages the connection, configuration, reading, and recording of data from a Digit sensor.
    """

    def __init__(self, config: DigitConfig):
        super().__init__(config=config)
        self.sensor: Digit | None = None

    def connect(self):
        """Establish a connection to the physical Digit sensor."""
        self.sensor = Digit(serial=self.get('serial_id'), name=self.get('sensor_name'))
        self.sensor.connect()

        # Configure the digit according to the config
        self.set('resolution', self.get('resolution'))
        self.set('rgb', self.get('rgb'))

    def set(self, attr: str, value: Any) -> Any:
        """
        Configures sensor settings like resolution, frame rate (FPS), intensity, etc.
        """
        if attr == 'resolution':
            self._config.resolution = value
            self.sensor.set_resolution(Digit.STREAMS[self.get('resolution')])

        elif attr == 'fps':
            self._config.set_fps(fps=value)
            self.sensor.set_fps(self.get('fps'))

        elif attr == 'rgb':
            self._config.rgb = value
            self.sensor.set_intensity_rgb(*value)

        else:
            print(f"Unsupported attribute '{attr}'")

    def disconnect(self):
        """
        Disconnects the sensor, stopping any ongoing threads and releasing resources.
        """
        super().disconnect()
        self.sensor.disconnect()

    @TouchSensor.data_source('camera', frequency=30)
    def read_camera(self):
        while True:
            yield self.sensor.get_frame()
