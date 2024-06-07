from enum import Enum
from opentouch_interface.sensors.digit_sensor import DigitSensor


class OpentouchInterface:
    class SensorType(Enum):
        DIGIT = "Digit"

    def __new__(cls, sensor_type: 'OpentouchInterface.SensorType', *args, **kwargs):
        if sensor_type == OpentouchInterface.SensorType.DIGIT:
            return DigitSensor()
        return super().__new__(cls)
