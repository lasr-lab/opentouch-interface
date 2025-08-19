from typing import Any

from opentouch_interface.core.registries.class_registries import SensorClassRegistry
from opentouch_interface.core.sensors.interfaces.gelsight_interface import GelSightMiniCamera
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.core.validation.sensors.gelsight_config import GelSightConfig


@SensorClassRegistry.register_sensor('GelSight Mini')
class GelSightMiniSensor(TouchSensor):
    """
    A class representing a GelSight Mini sensor, inheriting from `TouchSensor`.
    """

    def __init__(self, config: GelSightConfig):
        super().__init__(config=config)
        self.sensor: GelSightMiniCamera | None = None

    def connect(self):
        self.sensor = GelSightMiniCamera()
        self.sensor.connect()

    def set(self, attr: str, value: Any) -> Any:
        """
        The GelSight Mini sensor does not support setting any sensor values.
        """
        print(f'Unsupported attr \'{attr}\'')

    def disconnect(self) -> None:
        """Stops any ongoing threads and disconnects the sensor."""
        super().disconnect()
        self.sensor.disconnect()

    @TouchSensor.data_source('camera', frequency=30)
    def read_camera(self):
        while True:
            yield self.sensor.get_frame()
