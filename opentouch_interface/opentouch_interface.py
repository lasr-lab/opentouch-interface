from enum import Enum
from opentouch_interface.sensors.digit import DigitSensor
from opentouch_interface.sensors.gelsight_mini import GelsightMiniSensor


class OpentouchInterface:
    class SensorType(Enum):
        DIGIT = "Digit"
        GELSIGHT_MINI = "Gelsight Mini"

    def __new__(cls, sensor_type: 'OpentouchInterface.SensorType', *args, **kwargs):
        if sensor_type == OpentouchInterface.SensorType.DIGIT:
            return DigitSensor()
        elif sensor_type == OpentouchInterface.SensorType.GELSIGHT_MINI:
            return GelsightMiniSensor()
        return super().__new__(cls)
