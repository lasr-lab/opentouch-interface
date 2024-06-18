from opentouch_interface.sensors.digit import DigitSensor
from opentouch_interface.sensors.gelsight_mini import GelsightMiniSensor
from opentouch_interface.touch_sensor import TouchSensor


class OpentouchInterface:

    def __new__(cls, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            return DigitSensor(TouchSensor.SensorType.DIGIT)
        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            return GelsightMiniSensor(TouchSensor.SensorType.GELSIGHT_MINI)
        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
